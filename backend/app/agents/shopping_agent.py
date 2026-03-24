from app.domains.recommendation import RecommendationAgent


class ShoppingAgent:
    def __init__(self):
        self.recommendation_agent = RecommendationAgent()

    def handle(self, user_query: str, user_profile: dict = None):
        if user_profile is None:
            user_profile = {
                "preferred_brand": [],
                "budget_range": [0, 999999]
            }

        # 直接调用 RecommendationAgent
        results = self.recommendation_agent.recommend(user_query, user_profile)

        # 输出结构化结果（可选精简）
        recommendations = []
        for item in results:
            recommendations.append({
                "name": item["name"],
                "price": item["price"],
                "brand": item.get("brand", ""),
                "reason": item.get("reason", "")
            })

        return recommendations
