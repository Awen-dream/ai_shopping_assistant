import json
from typing import Dict

from app.domains.query_understanding.model import (
    clean_json,
    normalize_intent,
    parse_rule_based_intent,
)
from app.services.llm_client import get_llm_client, get_llm_model


class IntentAgent:
    """
    将用户自然语言查询解析成标准用户画像/意图。
    """

    def __init__(self, llm=None):
        self.llm = llm

    def rule_based_intent(self, query: str) -> Dict:
        return parse_rule_based_intent(query)

    def parse_intent(self, query: str) -> Dict:
        fallback_intent = self.rule_based_intent(query)
        llm = self.llm if self.llm is not None else get_llm_client()
        if llm is None:
            return normalize_intent(fallback_intent)

        prompt = f"""
请将用户查询解析为严格 JSON，不要返回 markdown：
查询："{query}"

返回格式：
{{
  "preferred_brand": [],
  "budget_range": [0, 15000],
  "interests": [],
  "category": "",
  "preferred_categories": [],
  "price_sensitivity": "medium",
  "scenario": "",
  "sort_preference": "balanced",
  "urgency": "normal",
  "fulfillment_preference": "standard",
  "required_features": []
}}
        """
        try:
            resp = llm.chat.completions.create(
                model=get_llm_model(),
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            text = clean_json(resp.choices[0].message.content)
            parsed = json.loads(text)
            merged = fallback_intent.copy()
            merged.update(parsed)
            return normalize_intent(merged)
        except Exception:
            return normalize_intent(fallback_intent)

    def classify_intent(self, query: str, products: list | None = None) -> str | None:
        intent = self.parse_intent(query)
        category = intent.get("category")
        if not category:
            return None
        if not products:
            return category

        valid_categories = {product.get("category") for product in products}
        return category if category in valid_categories else None
