import json
import re
from typing import Dict

from app.services.llm_client import get_llm_client, get_llm_model


DEFAULT_PROFILE = {
    "preferred_brand": [],
    "budget_range": [0, 15000],
    "interests": [],
    "category": "",
}

CATEGORY_KEYWORDS = {
    "手机": ["手机", "iphone", "小米", "华为", "oppo", "vivo", "拍照手机"],
    "笔记本": ["笔记本", "电脑", "laptop", "macbook", "轻薄本"],
    "耳机": ["耳机", "headphones", "airpods", "降噪", "xm5"],
}

BRAND_KEYWORDS = {
    "Apple": ["apple", "iphone", "macbook", "airpods", "苹果"],
    "Sony": ["sony", "索尼", "xm5"],
    "Dell": ["dell", "戴尔"],
    "Adidas": ["adidas", "阿迪达斯"],
    "Huawei": ["huawei", "华为"],
    "Xiaomi": ["xiaomi", "小米"],
}

INTEREST_KEYWORDS = {
    "轻便": ["轻便", "轻薄", "便携"],
    "降噪": ["降噪", "安静"],
    "拍照": ["拍照", "影像"],
    "办公": ["办公", "生产力"],
}


def _clean_json(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def _extract_budget_range(query: str) -> list[int]:
    query_lower = query.lower()

    between_match = re.search(r"(\d{3,6})\s*[-到~]\s*(\d{3,6})", query_lower)
    if between_match:
        low, high = sorted([int(between_match.group(1)), int(between_match.group(2))])
        return [low, high]

    under_match = re.search(r"(\d{3,6})\s*(以内|以下|预算内|之内)", query_lower)
    if under_match:
        return [0, int(under_match.group(1))]

    budget_match = re.search(r"(预算|价格|价位)\s*(\d{3,6})", query_lower)
    if budget_match:
        value = int(budget_match.group(2))
        return [0, value]

    return DEFAULT_PROFILE["budget_range"][:]


def _extract_category(query: str) -> str:
    query_lower = query.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return category
    return ""


def _extract_brands(query: str) -> list[str]:
    query_lower = query.lower()
    brands = []
    for brand, keywords in BRAND_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            brands.append(brand)
    return brands


def _extract_interests(query: str) -> list[str]:
    query_lower = query.lower()
    interests = []
    for interest, keywords in INTEREST_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            interests.append(interest)
    return interests


def _normalize_intent(intent: dict | None) -> Dict:
    normalized = DEFAULT_PROFILE.copy()
    if intent:
        normalized.update(intent)

    preferred_brand = normalized.get("preferred_brand") or []
    if isinstance(preferred_brand, str):
        preferred_brand = [preferred_brand]

    budget_range = normalized.get("budget_range") or DEFAULT_PROFILE["budget_range"][:]
    if not isinstance(budget_range, list) or len(budget_range) != 2:
        budget_range = DEFAULT_PROFILE["budget_range"][:]

    interests = normalized.get("interests") or []
    if isinstance(interests, str):
        interests = [interests]

    normalized["preferred_brand"] = preferred_brand
    normalized["budget_range"] = [int(budget_range[0]), int(budget_range[1])]
    normalized["interests"] = interests
    normalized["category"] = normalized.get("category") or ""
    return normalized


class IntentAgent:
    """
    将用户自然语言查询解析成标准用户画像/意图
    """

    def __init__(self, llm=None):
        self.llm = llm

    def rule_based_intent(self, query: str) -> Dict:
        return {
            "preferred_brand": _extract_brands(query),
            "budget_range": _extract_budget_range(query),
            "interests": _extract_interests(query),
            "category": _extract_category(query),
        }

    def parse_intent(self, query: str) -> Dict:
        """
        返回结构化用户画像：
        - preferred_brand
        - budget_range
        - interests
        - category
        """
        fallback_intent = self.rule_based_intent(query)
        llm = self.llm if self.llm is not None else get_llm_client()
        if llm is None:
            return _normalize_intent(fallback_intent)

        prompt = f"""
请将用户查询解析为严格 JSON，不要返回 markdown：
查询："{query}"

返回格式：
{{
  "preferred_brand": [],
  "budget_range": [0, 15000],
  "interests": [],
  "category": ""
}}
        """
        try:
            resp = llm.chat.completions.create(
                model=get_llm_model(),
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            text = _clean_json(resp.choices[0].message.content)
            parsed = json.loads(text)
            merged = fallback_intent.copy()
            merged.update(parsed)
            return _normalize_intent(merged)
        except Exception:
            return _normalize_intent(fallback_intent)

    def classify_intent(self, query: str, products: list | None = None) -> str | None:
        intent = self.parse_intent(query)
        category = intent.get("category")
        if not category:
            return None
        if not products:
            return category

        valid_categories = {product.get("category") for product in products}
        return category if category in valid_categories else None
