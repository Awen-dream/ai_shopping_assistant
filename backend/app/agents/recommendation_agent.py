import numpy as np
import re
from typing import List, Dict

from app.agents.intent_agent import CATEGORY_KEYWORDS as INTENT_CATEGORY_KEYWORDS
from app.agents.intent_agent import INTEREST_KEYWORDS, IntentAgent
from app.services.product_service import list_products
from app.services.vector_store_service import build_product_text, create_vector_store

# =========================
# 本地规则类别映射
# =========================
CATEGORY_KEYWORDS = {
    "手机": ["iphone", "小米", "华为", "oppo", "vivo", "手机"],
    "笔记本": ["macbook", "笔记本", "laptop", "surface", "电脑", "轻薄本"],
    "耳机": ["耳机", "headphones", "wh-1000xm5", "airpods"]
}

for category, keywords in INTENT_CATEGORY_KEYWORDS.items():
    CATEGORY_KEYWORDS.setdefault(category, [])
    CATEGORY_KEYWORDS[category] = list(dict.fromkeys(CATEGORY_KEYWORDS[category] + keywords))

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
    def __init__(self, products: List[Dict], model_name: str | None = None):
        self.products = products
        self.texts = [self._product_text(product) for product in products]
        self.vector_store = create_vector_store(products)
        self.model = self.vector_store.model
        self.index = self.vector_store.index
        self.ready = self.vector_store.ready

    @staticmethod
    def _product_text(product: Dict) -> str:
        return build_product_text(product)

    @staticmethod
    def _extract_terms(query: str) -> list[str]:
        query_lower = query.lower()
        alnum_terms = re.findall(r"[a-z0-9]+", query_lower)
        terms = [query_lower, *alnum_terms]
        for category, keywords in CATEGORY_KEYWORDS.items():
            if category.lower() in query_lower or any(keyword in query_lower for keyword in keywords):
                terms.append(category.lower())
                terms.extend(keywords)
        for interest, keywords in INTEREST_KEYWORDS.items():
            if interest in query_lower or any(keyword in query_lower for keyword in keywords):
                terms.append(interest.lower())
                terms.extend(keywords)
        return list(dict.fromkeys(term for term in terms if term))

    def _fallback_search(self, query: str, topk=20):
        terms = self._extract_terms(query)
        scored = []
        for product, text in zip(self.products, self.texts):
            lowered = text.lower()
            score = sum(1 for term in terms if term in lowered)
            if score:
                scored.append((product, float(score)))

        if not scored:
            scored = [(product, 0.1) for product in self.products]

        return sorted(scored, key=lambda item: item[1], reverse=True)[:topk]

    def search(self, query: str, topk=20):
        if not self.ready:
            return self._fallback_search(query, topk=topk)

        results = self.vector_store.search(query, topk=topk)
        return results or self._fallback_search(query, topk=topk)

# =========================
# Keyword Recall
# =========================
class KeywordRetriever:
    def __init__(self, products):
        self.products = products

    def search(self, query):
        query = query.lower()
        keywords = Retriever._extract_terms(query)

        results = []
        for p in self.products:
            text = Retriever._product_text(p).lower()
            score = sum(1 for keyword in keywords if keyword in text)
            if score:
                results.append((p, float(score)))

        return sorted(results, key=lambda item: item[1], reverse=True)


class QueryContextBuilder:
    def build(self, query: str, user_profile: dict | None = None):
        user_profile = user_profile or {}
        category = user_profile.get("category") or classify_intent_rule(query) or ""
        preferred_brand = user_profile.get("preferred_brand") or []
        interests = user_profile.get("interests") or []

        terms = Retriever._extract_terms(query)
        if category:
            terms.append(category.lower())
            terms.extend(CATEGORY_KEYWORDS.get(category, []))
        for interest in interests:
            terms.append(interest.lower())
            terms.extend(INTEREST_KEYWORDS.get(interest, []))

        return {
            "raw_query": query,
            "category": category,
            "preferred_brand": preferred_brand,
            "budget_range": user_profile.get("budget_range", [0, 999999]),
            "interests": interests,
            "preferred_categories": user_profile.get("preferred_categories", []),
            "price_sensitivity": user_profile.get("price_sensitivity", "medium"),
            "terms": list(dict.fromkeys(term for term in terms if term)),
        }

# =========================
# Category Embedding
# =========================
class CategoryEmbedding:
    def __init__(self, products: List[Dict], model):
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
        self.category_embeddings = None

        if not self.model or not self.category_names:
            return

        category_texts_merged = [' '.join(texts) for texts in self.category_texts.values()]
        self.category_embeddings = self.model.encode(category_texts_merged, normalize_embeddings=True)

    def classify_query(self, query: str):
        if self.category_embeddings is None:
            return None

        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        sims = np.dot(self.category_embeddings, q_emb)
        if len(sims) == 0:
            return None
        best_idx = np.argmax(sims)
        if sims[best_idx] > 0.3:
            return self.category_names[best_idx]
        return None

    def get_scores(self, query):
        if self.category_embeddings is None:
            return {}

        q_emb = self.model.encode([query], normalize_embeddings=True)[0]
        sims = np.dot(self.category_embeddings, q_emb)
        return dict(zip(self.category_names, sims))

# =========================
# Ranker
# =========================
class Ranker:
    def __init__(self, weights=None):
        self.weights = weights or {
            'keyword': 0.42,
            'vector': 0.18,
            'interest': 0.15,
            'category': 0.10,
            'brand': 0.08,
            'budget': 0.04,
            'rating': 0.03,
        }

    @staticmethod
    def _score_product(product, query_context, keyword_score, vector_score):
        product_text = Retriever._product_text(product).lower()
        matched_terms = [term for term in query_context["terms"] if term in product_text]
        matched_interests = [interest for interest in query_context["interests"] if interest in product_text]

        category_match = 1 if query_context["category"] and product.get("category") == query_context["category"] else 0
        brand_match = 1 if query_context["preferred_brand"] and product.get("brand") in query_context["preferred_brand"] else 0
        budget_low, budget_high = query_context["budget_range"]
        budget_match = 1 if budget_low <= product.get("price", 0) <= budget_high else 0
        rating_score = min(product.get("rating", 0) / 5.0, 1.0)
        interest_score = min(len(matched_interests) / max(len(query_context["interests"]), 1), 1.0) if query_context["interests"] else 0.0
        sales_score = min(product.get("monthly_sales", 0) / 10000.0, 1.0)
        promotion_score = 1.0 if product.get("promotion_tag") else 0.0
        inventory_score = min(product.get("inventory_total", 0) / 200.0, 1.0)

        detail = {
            "matched_terms": matched_terms,
            "matched_interests": matched_interests,
            "category_match": bool(category_match),
            "brand_match": bool(brand_match),
            "budget_match": bool(budget_match),
            "interest_score": interest_score,
            "rating_score": rating_score,
            "sales_score": sales_score,
            "promotion_score": promotion_score,
            "inventory_score": inventory_score,
            "keyword_score": keyword_score,
            "vector_score": vector_score,
        }
        return detail

    def score(self, product, query_context, keyword_score, vector_score):
        detail = self._score_product(product, query_context, keyword_score, vector_score)
        score = (
            self.weights["keyword"] * keyword_score +
            self.weights["vector"] * vector_score +
            self.weights["interest"] * detail["interest_score"] +
            self.weights["category"] * (1.0 if detail["category_match"] else 0.0) +
            self.weights["brand"] * (1.0 if detail["brand_match"] else 0.0) +
            self.weights["budget"] * (1.0 if detail["budget_match"] else 0.0) +
            self.weights["rating"] * detail["rating_score"] +
            0.04 * detail["sales_score"] +
            0.03 * detail["promotion_score"] +
            0.02 * detail["inventory_score"]
        )
        return score, detail

    def rank(self, items, query_context):
        ranked = []
        for item in items:
            final_score, detail = self.score(
                item["product"],
                query_context,
                item.get("keyword_score", 0.0),
                item.get("vector_score", 0.0),
            )
            ranked.append((item["product"], final_score, detail))
        return sorted(ranked, key=lambda x: x[1], reverse=True)

# =========================
# Reason Generator
# =========================
class ReasonGenerator:
    def __init__(self, llm=None):
        self.llm = llm

    def generate_batch(self, ranked_items, user_profile):
        return [self.default_reason(product, user_profile, detail) for product, _, detail in ranked_items]

    def default_reason(self, product, user_profile, detail):
        reasons = []
        if detail.get("category_match"):
            reasons.append(f"匹配你要找的{product.get('category')}")
        if detail.get("brand_match"):
            reasons.append(f"命中品牌偏好 {product.get('brand')}")
        if detail.get("matched_interests"):
            reasons.append(f"命中诉求：{'/'.join(detail['matched_interests'])}")
        if detail.get("budget_match"):
            reasons.append("价格在预算范围内")
        if product.get("promotion_tag"):
            reasons.append(f"当前活动：{product.get('promotion_tag')}")
        if product.get("monthly_sales", 0) >= 3000:
            reasons.append(f"近月销量 {product.get('monthly_sales')}")
        if product.get("rating", 0) >= 4.8:
            reasons.append(f"评分 {product.get('rating')}")
        if detail.get("matched_terms"):
            keywords = "/".join(detail["matched_terms"][:2])
            reasons.append(f"关键词命中：{keywords}")

        unique_reasons = []
        for reason in reasons:
            if reason not in unique_reasons:
                unique_reasons.append(reason)

        return "；".join(unique_reasons[:4]) or "与当前查询较匹配"

# =========================
# Main Agent
# =========================
class RecommendationAgent:
    def __init__(self):
        self.products = list_products()
        self.vector_retriever = Retriever(self.products)
        self.keyword_retriever = KeywordRetriever(self.products)
        self.query_context_builder = QueryContextBuilder()
        self.model = self.vector_retriever.model
        self.category_embedding = CategoryEmbedding(self.products, self.model)
        self.ranker = Ranker()
        self.reasoner = ReasonGenerator()
        self.intent_agent = IntentAgent()

    def hybrid_recall(self, query, query_context):
        vector_results = self.vector_retriever.search(query, topk=20)
        keyword_results = self.keyword_retriever.search(query)
        merged = {}

        max_keyword_score = max((score for _, score in keyword_results), default=1.0)
        vector_scores = [score for _, score in vector_results]
        max_vector_score = max(vector_scores, default=1.0)
        min_vector_score = min(vector_scores, default=0.0)

        for product, score in keyword_results:
            merged[product["id"]] = {
                "product": product,
                "keyword_score": min(score / max_keyword_score, 1.0),
                "vector_score": 0.0,
            }

        for product, score in vector_results:
            if max_vector_score == min_vector_score:
                normalized_vector_score = 1.0 if max_vector_score > 0 else 0.0
            else:
                normalized_vector_score = (score - min_vector_score) / (max_vector_score - min_vector_score)
            merged.setdefault(
                product["id"],
                {"product": product, "keyword_score": 0.0, "vector_score": 0.0},
            )
            merged[product["id"]]["vector_score"] = max(
                merged[product["id"]]["vector_score"],
                normalized_vector_score,
            )

        candidates = list(merged.values()) or [
            {"product": product, "keyword_score": 0.0, "vector_score": 0.0}
            for product in self.products
        ]

        if query_context["category"]:
            candidates = [
                item for item in candidates
                if item["product"].get("category") == query_context["category"]
            ] or candidates

        if query_context["preferred_brand"]:
            brand_matched = [
                item for item in candidates
                if item["product"].get("brand") in query_context["preferred_brand"]
            ]
            if brand_matched:
                candidates = brand_matched

        if query_context["preferred_categories"] and not query_context["category"]:
            preferred_category_candidates = [
                item for item in candidates
                if item["product"].get("category") in query_context["preferred_categories"]
            ]
            if preferred_category_candidates:
                candidates = preferred_category_candidates

        return candidates

    def recommend(self, query: str, user_profile=None, topk=5):
        user_profile = user_profile or self.intent_agent.parse_intent(query)
        if not user_profile.get("category"):
            user_profile["category"] = self.category_embedding.classify_query(query) or classify_intent_rule(query) or ""

        query_context = self.query_context_builder.build(query, user_profile)
        recalled = self.hybrid_recall(query, query_context)
        ranked = self.ranker.rank(recalled, query_context)

        top_ranked_items = ranked[:topk]
        reasons = self.reasoner.generate_batch(top_ranked_items, user_profile)

        results = []
        for (product, score, detail), reason in zip(top_ranked_items, reasons):
            best_match_score = round(score, 4)
            matched_features = {
                "matched_terms": detail.get("matched_terms", [])[:4],
                "matched_interests": detail.get("matched_interests", []),
                "category_match": detail.get("category_match", False),
                "brand_match": detail.get("brand_match", False),
                "budget_match": detail.get("budget_match", False),
            }

            p = product
            item = p.copy()
            item['reason'] = reason
            item['match_score'] = best_match_score
            item['matched_features'] = matched_features
            results.append(item)

        return results

    def get_vector_status(self):
        return self.vector_retriever.vector_store.status()

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
