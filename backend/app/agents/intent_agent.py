from typing import Dict
from app.services.llm_client import get_llm_client
import json

# 使用本地/云 OpenAI API 或其他 LLM
client = get_llm_client()

class IntentAgent:
    """
    将用户自然语言查询解析成标准用户画像/意图
    """

    def __init__(self, llm=None):
        self.llm = llm or client

    def parse_intent(self, query: str) -> Dict:
        """
        返回结构化用户画像：
        - preferred_brand
        - budget_range
        - interests
        - category
        """
        prompt = f"""
        请将用户查询 "{query}" 解析为JSON格式：
        {{
            "preferred_brand": [],
            "budget_range": [0, 15000],
            "interests": [],
            "category": ""
        }}
        """
        try:
            resp = self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            text = resp.choices[0].message.content
            return json.loads(text)
        except Exception as e:
            print("LLM解析失败，使用默认策略:", e)
            return {"preferred_brand": [], "budget_range": [0,15000], "interests": [], "category": ""}

    def classify_intent(self, query: str, products: list) -> str:
        """
        通过解析完整用户画像获取类别
        """
        intent = self.parse_intent(query)
        category = intent.get('category')
        if category and category in [p['category'] for p in products]:
            return category
        return None