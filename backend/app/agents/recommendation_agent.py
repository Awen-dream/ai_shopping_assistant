import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# 读取商品数据
with open("backend/data/products.json") as f:
    products = json.load(f)

# 构建向量索引
model = SentenceTransformer('all-MiniLM-L6-v2')
product_texts = [p["name"] + " " + p["description"] for p in products]
embeddings = model.encode(product_texts)
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(np.array(embeddings))

def vector_search(query: str, topk=10):
    q_emb = model.encode([query])
    D, I = index.search(np.array(q_emb), topk)
    return [products[i] for i in I[0]]

def rank_products(products_list, user_profile):
    def score(p):
        brand_score = 1 if p["brand"] in user_profile["preferred_brand"] else 0
        price_score = 1 if user_profile["budget_range"][0] <= p["price"] <= user_profile["budget_range"][1] else 0
        return p["rating"]*0.5 + brand_score*0.3 + price_score*0.2
    return sorted(products_list, key=score, reverse=True)

def generate_reason(product, user_profile):
    reasons = []
    if product["brand"] in user_profile["preferred_brand"]:
        reasons.append("Matches your preferred brand")
    if product["price"] <= user_profile["budget_range"][1]:
        reasons.append("Within your budget")
    reasons.append(f"High rating {product['rating']}")
    return ", ".join(reasons)