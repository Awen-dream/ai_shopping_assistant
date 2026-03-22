from .agents.inventory_agent import InventoryAgent
from .agents.price_agent import PriceAgent
from .agents.recommendation_agent import RecommendationAgent
from .agents.search_agent import SearchAgent
from .agents.intent_agent import IntentAgent
from .agents.image_search_agent import ImageSearchAgent
from .services.user_profile_service import get_user_profile, merge_profiles

class MultiAgentCoordinator:
    def __init__(self):
        self.recommend_agent = RecommendationAgent()
        self.search_agent = SearchAgent()
        self.price_agent = PriceAgent()
        self.inventory_agent = InventoryAgent()
        self.intent_agent = IntentAgent()
        self.image_agent = ImageSearchAgent(
            self.recommend_agent.vector_retriever.index,
            self.recommend_agent.products
        )

    def handle_query(self, query: str = "", image_path: str | None = None, user_id: str | None = None):
        stored_profile = get_user_profile(user_id) if user_id else None
        parsed_profile = self.intent_agent.parse_intent(query) if query else {}
        user_profile = merge_profiles(stored_profile, parsed_profile)

        if image_path:
            # 图片搜索优先
            recommended = self.image_agent.search_by_image(image_path)
            for product in recommended:
                product.setdefault("reason", "Image-based fallback recommendation")
        else:
            recommended = self.recommend_agent.recommend(query, user_profile)

        # 1️⃣ 推荐热门商品
        #recommended = self.recommend_agent.recommend(query, user_profile)

        # 2️⃣ 搜索匹配商品（多商家）
        searched = self.search_agent.search(recommended)

        # 3️⃣ 比价
        priced = self.price_agent.compare(searched, user_profile=user_profile)

        # 4️⃣ 检查库存
        stocked = self.inventory_agent.filter_stock(priced, user_profile=user_profile)

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
