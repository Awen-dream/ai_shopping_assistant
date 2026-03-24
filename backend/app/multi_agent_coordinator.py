from .domains.inventory import apply_inventory_rules, create_inventory_agent
from .domains.multimodal import create_image_search_agent, search_products_by_image
from .domains.pricing import compare_prices, create_price_agent
from .domains.profiles import get_user_profile, merge_profiles
from .domains.query_understanding import create_intent_agent
from .domains.recommendation import create_recommendation_agent, create_search_agent, search_market_offers

class MultiAgentCoordinator:
    def __init__(self):
        self.recommend_agent = create_recommendation_agent()
        self.search_agent = create_search_agent()
        self.price_agent = create_price_agent()
        self.inventory_agent = create_inventory_agent()
        self.intent_agent = create_intent_agent()
        self.image_agent = create_image_search_agent(
            self.recommend_agent.vector_retriever.index,
            self.recommend_agent.products
        )

    def handle_query(self, query: str = "", image_path: str | None = None, user_id: str | None = None):
        stored_profile = get_user_profile(user_id) if user_id else None
        parsed_profile = self.intent_agent.parse_intent(query) if query else {}
        user_profile = merge_profiles(stored_profile, parsed_profile)

        if image_path:
            recommended = search_products_by_image(self.image_agent, image_path)
            for product in recommended:
                product.setdefault("reason", "Image-based fallback recommendation")
        else:
            recommended = self.recommend_agent.recommend(query, user_profile)

        searched = search_market_offers(recommended, user_profile=user_profile)
        priced = compare_prices(searched, user_profile=user_profile)
        stocked = apply_inventory_rules(priced, user_profile=user_profile)

        # 去重：按商品 id
        seen = set()
        unique_results = []
        for p in stocked:
            if p["id"] not in seen:
                unique_results.append(p)
                seen.add(p["id"])

        # 5️⃣ 保证前端安全字段
        safe_products = []
        for p in unique_results:
            safe_products.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "brand": p.get("brand"),
                "category": p.get("category"),
                "subcategory": p.get("subcategory"),
                "rating": p.get("rating"),
                "price": p.get("price"),
                "monthly_sales": p.get("monthly_sales"),
                "promotion_tag": p.get("promotion_tag"),
                "inventory_total": p.get("inventory_total"),
                "reason": p.get("reason", ""),
                "match_score": p.get("match_score"),
                "matched_features": p.get("matched_features", {}),
                "best_offer": p.get("best_offer"),
                "available": p.get("available", []),
                "search_results": p.get("search_results", [])
            })

        return safe_products

    def get_vector_status(self):
        return self.recommend_agent.get_vector_status()
