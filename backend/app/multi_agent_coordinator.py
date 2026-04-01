from .domains.inventory import apply_inventory_rules, create_inventory_agent
from .domains.multimodal import create_image_search_agent, search_products_by_image
from .domains.pipeline import build_safe_product_payload, normalize_intent_profile, normalize_pipeline_products
from .domains.pricing import compare_prices, create_price_agent
from .domains.profiles import get_user_profile, merge_profiles
from .domains.query_understanding.service import create_intent_agent
from .domains.recommendation.service import (
    create_recommendation_agent,
    create_search_agent,
    recommend_with_agent,
    search_market_offers,
)

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
        user_profile = normalize_intent_profile(
            merge_profiles(stored_profile, parsed_profile),
            raw_query=query,
        )

        if image_path:
            recommended = normalize_pipeline_products(
                search_products_by_image(self.image_agent, image_path),
                stage="recommended",
            )
            for product in recommended:
                if not product.get("reason"):
                    product["reason"] = "Image-based fallback recommendation"
        else:
            recommended = recommend_with_agent(self.recommend_agent, query, user_profile=user_profile)

        searched = search_market_offers(recommended, user_profile=user_profile, agent=self.search_agent)
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
            safe_products.append(build_safe_product_payload(p))

        return safe_products

    def get_vector_status(self):
        return self.recommend_agent.get_vector_status()
