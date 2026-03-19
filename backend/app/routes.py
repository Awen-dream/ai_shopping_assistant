from fastapi import APIRouter, Query
from .agents.shopping_agent import shopping_agent

router = APIRouter()

@router.get("/recommend")
def recommend_products(query: str = Query(..., description="用户查询关键词")):
    # 示例用户画像
    user_profile = {
        "user_id": 1001,
        "preferred_brand": ["Nike", "Adidas"],
        "budget_range": [500, 1200],
        "interests": ["running", "fitness"]
    }
    result = shopping_agent(query, user_profile)
    return {"query": query, "recommendations": result}