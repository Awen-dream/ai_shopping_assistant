import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict

from app.agents.intent_agent import IntentAgent
from app.services.llm_client import get_llm_client

# =========================
# 本地规则类别映射
# =========================
CATEGORY_KEYWORDS = {
    "手机": ["iphone", "小米", "华为", "oppo", "vivo", "手机"],
    "笔记本": ["macbook", "笔记本", "laptop", "surface"],
    "耳机": ["耳机", "headphones", "wh-1000xm5", "airpods"]
}

def classify_intent_rule(query: str) -> str:
    q = query.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in q for kw in kws):
            return cat
    return None

# =========================
# Retriever
# =========================
class Retriever:
    def __init__(self, products: List[Dict], model_name='all-MiniLM-L6-v2'):
        self.products = products
        self.model = SentenceTransformer(model_name)

        self.texts = [p['name'] + ' ' + p.get('description', '') for p in products]
        self.embeddings = self.model.encode(self.texts, normalize_embeddings=True)

        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(self.embeddings)

    def search(self, query: str, topk=20):
        q_emb = self.model.encode([query], normalize_embeddings=True)
        scores, idxs = self.index.search(q_emb, topk)
        return [(self.products[i], float(scores[0][j])) for j, i in enumerate(idxs[0])]

# =========================
# Keyword Recall
# =========================
class KeywordRetriever:
    def __init__(self, products):
        self.products = products

    def search(self, query):
        query = query.lower()
        keywords = query.split()

        results = []
        for p in self.products:
            text = (p['name'] + ' ' + p.get('description', '')).lower()
            if any(k in text for k in keywords):
                results.append((p, 1.0))  # keyword命中给高分

        return results

# =========================
# Category Embedding
# =========================
class CategoryEmbedding:
    def __init__(self, products: List[Dict], model: SentenceTransformer):
        self.model = model
        self.category_texts = {}
        for p in products:
            cat = p.get('category')
            if not cat:
                continue
            cat_lower = cat.lower()
            text = p['name'] + ' ' + p.get('description', '')
            if cat_lower not in self.category_texts:
                self.category_texts[cat_lower] = []
            self.category_texts[cat_lower].append(text)

        self.category_names = list(self.category_texts.keys())
        category_texts_merged = [' '.join(texts) for texts in self.category_texts.values()]
        self.category_embeddings = self.model.encode(category_texts_merged, normalize_embeddings=True)

    def get_scores(self, query):
        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        sims = np.dot(self.category_embeddings, q_emb)
        return dict(zip(self.category_names, sims))

# =========================
# Ranker
# =========================
class Ranker:
    def __init__(self, weights=None):
        self.weights = weights or {
            'rating': 0.4,
            'brand': 0.2,
            'price': 0.2,
            'similarity': 0.6
        }

    def score(self, product, sim, category_sim, user_profile):
        brand_score = 1 if product.get('brand') in user_profile.get('preferred_brand', []) else 0
        price_range = user_profile.get('budget_range', [0, 999999])
        price_score = 1 if price_range[0] <= product.get('price', 0) <= price_range[1] else 0

        base_score = (
            self.weights['rating'] * product.get('rating', 0) +
            self.weights['brand'] * brand_score +
            self.weights['price'] * price_score +
            self.weights['similarity'] * sim
        )

        return base_score * (0.5 + 0.5 * category_sim)  # category embedding 作为加分

    def rank(self, items, category_scores, user_profile):
        ranked = []
        for p, s in items:
            cat = p.get('category', '').lower()
            category_sim = category_scores.get(cat, 0)
            final_score = self.score(p, s, category_sim, user_profile)
            ranked.append((p, final_score))
        return sorted(ranked, key=lambda x: x[1], reverse=True)

# =========================
# Reason Generator
# =========================
class ReasonGenerator:
    def __init__(self, llm=None):
        self.llm = llm

    def generate_batch(self, products, user_profile):
        return [self.default_reason(p, user_profile) for p in products]

    def default_reason(self, product, user_profile):
        reasons = []
        if product.get('brand') in user_profile.get('preferred_brand', []):
            reasons.append('Preferred brand')
        if product.get('price', 0) <= user_profile.get('budget_range', [0, 999999])[1]:
            reasons.append('Within budget')
        reasons.append(f"Rating {product.get('rating', 0)}")
        return ', '.join(reasons)

# =========================
# Main Agent
# =========================
class RecommendationAgent:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_dir, '../../../data', 'sample_products.json')
        with open(data_path, 'r') as f:
            self.products = json.load(f)

        self.vector_retriever = Retriever(self.products)
        self.keyword_retriever = KeywordRetriever(self.products)
        self.model = self.vector_retriever.model
        self.category_embedding = CategoryEmbedding(self.products, self.model)
        self.ranker = Ranker()
        self.reasoner = ReasonGenerator()
        self.intent_agent = IntentAgent()
        llm_client = get_llm_client() if get_llm_client else None

    def hybrid_recall(self, query):
        vec_results = self.vector_retriever.search(query, topk=20)
        kw_results = self.keyword_retriever.search(query)
        merged = {}
        query_lower = query.lower()

        for p, s in vec_results:
            keyword_hit = any(k in (p['name'] + p.get('description', '')).lower() for k in query_lower.split())
            if keyword_hit:
                s += 1.0
            else:
                s *= 0.2
            merged[p['id']] = (p, s)

        for p, s in kw_results:
            merged[p['id']] = (p, max(s, merged.get(p['id'], (p, 0))[1]))

        return list(merged.values())

    def recommend(self, query: str, user_profile=None, topk=5):
        user_profile = user_profile or {'preferred_brand': [], 'budget_range': [0, 999999]}

        # Step1: LLM分类意图
        #intent_category = self.intent_agent.classify_intent(query, self.products)
        intent_category = classify_intent_rule(query)

        recalled = self.hybrid_recall(query)

        # Step2: 强制类别过滤
        if intent_category:
            recalled = [(p, s) for p, s in recalled if p.get('category', '').lower() == intent_category.lower()]

        # Step3: 计算类别相似度
        cat_scores = self.category_embedding.get_scores(query)
        # Step4: 排序
        ranked = self.ranker.rank(recalled, cat_scores, user_profile)

        top_items = [p for p, _ in ranked[:topk]]
        reasons = self.reasoner.generate_batch(top_items, user_profile)

        results = []
        for p, r in zip(top_items, reasons):
            item = p.copy()
            item['reason'] = r
            results.append(item)

        return results

# =========================
# Usage Example
# =========================
if __name__ == '__main__':
    agent = RecommendationAgent()

    user_profile = {
        'preferred_brand': ['Apple'],
        'budget_range': [5000, 15000]
    }

    res = agent.recommend('电脑', user_profile)
    for r in res:
        print(r)
