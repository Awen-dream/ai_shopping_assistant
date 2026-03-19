from .recommendation_agent import vector_search, rank_products, generate_reason

def shopping_agent(user_query: str, user_profile: dict):
    # 1. 检索商品
    candidates = vector_search(user_query)
    # 2. 排序
    ranked = rank_products(candidates, user_profile)
    # 3. 生成解释
    recommendations = []
    for item in ranked[:5]:
        recommendations.append({
            "name": item["name"],
            "price": item["price"],
            "brand": item["brand"],
            "reason": generate_reason(item, user_profile)
        })
    return recommendations