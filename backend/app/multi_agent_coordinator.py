from .agents.inventory_agent import InventoryAgent
from .agents.price_agent import PriceAgent
from .agents.recommendation_agent import RecommendationAgent
from .agents.search_agent import SearchAgent
from .agents.intent_agent import IntentAgent
from .agents.image_search_agent import ImageSearchAgent

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

    def handle_query(self, query: str = "", image_path: str | None = None):
        user_profile = self.intent_agent.parse_intent(query)

        if image_path:
            # 图片搜索优先
            recommended = self.image_agent.search_by_image(image_path)
        else:
            recommended = self.recommend_agent.recommend(query, user_profile)

        # 1️⃣ 推荐热门商品
        #recommended = self.recommend_agent.recommend(query, user_profile)

        # 2️⃣ 搜索匹配商品（多商家）
        searched = self.search_agent.search(recommended)

        # 3️⃣ 比价
        priced = self.price_agent.compare(searched)

        # 4️⃣ 检查库存
        stocked = self.inventory_agent.filter_stock(priced)

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
                "price": p.get("price"),
                "reason": p.get("reason", ""),
                "available": p.get("available", []),
                "search_results": p.get("search_results", [])
            })

        return safe_products

    def parse_user_intent(self, query: str):
        # 🔹 简单规则示例：关键词匹配兴趣/类别
        interests = []
        if "手机" in query or "轻便" in query:
            interests.append("轻便")
        if "降噪" in query or "耳机" in query:
            interests.append("降噪")
        return {
            "preferred_brand": ["Apple", "Sony", "Dell", "Adidas"],
            "budget_range": [0, 15000],
            "interests": interests
        }