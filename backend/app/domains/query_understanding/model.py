import re
from typing import Dict


DEFAULT_PROFILE = {
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
    "required_features": [],
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
    "Lenovo": ["lenovo", "联想", "thinkpad", "小新"],
    "Huawei": ["huawei", "华为"],
    "Xiaomi": ["xiaomi", "小米", "redmi"],
}

INTEREST_KEYWORDS = {
    "轻便": ["轻便", "轻薄", "便携"],
    "降噪": ["降噪", "安静"],
    "拍照": ["拍照", "影像", "vlog"],
    "办公": ["办公", "生产力", "商务"],
    "续航": ["续航", "待机", "电池"],
    "高性能": ["性能", "游戏", "流畅", "旗舰"],
    "性价比": ["性价比", "划算", "值", "便宜"],
}

SCENARIO_KEYWORDS = {
    "学生": ["学生", "宿舍", "上课", "学习", "校园"],
    "商务": ["商务", "出差", "差旅", "会议", "办公"],
    "通勤": ["通勤", "地铁", "公交", "上下班"],
    "摄影": ["摄影", "拍照", "影像", "vlog"],
    "游戏": ["游戏", "电竞", "高帧率"],
}

SORT_PREFERENCE_KEYWORDS = {
    "price": ["性价比", "便宜", "省钱", "划算", "低价", "优惠"],
    "performance": ["性能", "旗舰", "流畅", "高性能", "游戏"],
    "portability": ["轻薄", "便携", "通勤", "重量轻"],
    "camera": ["拍照", "影像", "人像", "长焦"],
    "battery": ["续航", "待机", "长续航"],
}

URGENCY_KEYWORDS = {
    "urgent": ["今天", "明天", "尽快", "马上", "立刻", "急用", "次日达"],
    "flexible": ["不着急", "慢慢来", "等等也行", "预售也可以"],
}

FULFILLMENT_PREFERENCE_KEYWORDS = {
    "fast_delivery": ["现货", "次日达", "当天", "马上", "尽快"],
    "presale_ok": ["预售也可以", "可以等", "不着急"],
}

FEATURE_KEYWORDS = {
    "降噪": ["降噪", "主动降噪"],
    "轻薄": ["轻薄", "轻便", "便携"],
    "拍照": ["拍照", "影像", "长焦"],
    "办公": ["办公", "生产力", "商务"],
    "续航": ["续航", "待机", "长续航"],
    "高性能": ["性能", "游戏", "流畅", "旗舰"],
    "学生": ["学生", "校园"],
    "性价比": ["性价比", "划算", "便宜"],
}


def clean_json(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return cleaned.strip()


def extract_budget_range(query: str) -> list[int]:
    query_lower = query.lower()

    between_match = re.search(r"(\d{3,6})\s*[-到~]\s*(\d{3,6})", query_lower)
    if between_match:
        low, high = sorted([int(between_match.group(1)), int(between_match.group(2))])
        return [low, high]

    around_match = re.search(r"(\d{3,6})\s*(左右|上下)", query_lower)
    if around_match:
        value = int(around_match.group(1))
        return [max(value - 1000, 0), value + 1000]

    under_match = re.search(r"(\d{3,6})\s*(以内|以下|预算内|之内)", query_lower)
    if under_match:
        return [0, int(under_match.group(1))]

    budget_match = re.search(r"(预算|价格|价位)\s*(\d{3,6})", query_lower)
    if budget_match:
        value = int(budget_match.group(2))
        return [0, value]

    return DEFAULT_PROFILE["budget_range"][:]


def extract_category(query: str) -> str:
    query_lower = query.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return category
    return ""


def extract_brands(query: str) -> list[str]:
    query_lower = query.lower()
    return [
        brand for brand, keywords in BRAND_KEYWORDS.items()
        if any(keyword in query_lower for keyword in keywords)
    ]


def extract_interests(query: str) -> list[str]:
    query_lower = query.lower()
    return [
        interest for interest, keywords in INTEREST_KEYWORDS.items()
        if any(keyword in query_lower for keyword in keywords)
    ]


def extract_required_features(query: str) -> list[str]:
    query_lower = query.lower()
    return [
        feature for feature, keywords in FEATURE_KEYWORDS.items()
        if any(keyword in query_lower for keyword in keywords)
    ]


def extract_scenario(query: str) -> str:
    query_lower = query.lower()
    for scenario, keywords in SCENARIO_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return scenario
    return ""


def extract_sort_preference(query: str) -> str:
    query_lower = query.lower()
    for preference, keywords in SORT_PREFERENCE_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return preference
    return "balanced"


def extract_urgency(query: str) -> str:
    query_lower = query.lower()
    for urgency, keywords in URGENCY_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return urgency
    return "normal"


def extract_fulfillment_preference(query: str) -> str:
    query_lower = query.lower()
    for preference, keywords in FULFILLMENT_PREFERENCE_KEYWORDS.items():
        if any(keyword in query_lower for keyword in keywords):
            return preference
    return "standard"


def extract_price_sensitivity(query: str, budget_range: list[int], sort_preference: str) -> str:
    query_lower = query.lower()
    if sort_preference == "price" or any(
        keyword in query_lower for keyword in ["性价比", "便宜", "省钱", "划算", "优惠"]
    ):
        return "high"
    if any(keyword in query_lower for keyword in ["旗舰", "高端", "顶配", "不差钱"]):
        return "low"
    if budget_range[1] <= 5000:
        return "high"
    if budget_range[1] >= 10000:
        return "low"
    return "medium"


def normalize_str_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value if item]


def normalize_intent(intent: dict | None) -> Dict:
    normalized = DEFAULT_PROFILE.copy()
    if intent:
        normalized.update(intent)

    budget_range = normalized.get("budget_range") or DEFAULT_PROFILE["budget_range"][:]
    if not isinstance(budget_range, list) or len(budget_range) != 2:
        budget_range = DEFAULT_PROFILE["budget_range"][:]

    category = normalized.get("category") or ""
    preferred_categories = normalize_str_list(normalized.get("preferred_categories"))
    if category and category not in preferred_categories:
        preferred_categories.insert(0, category)

    normalized["preferred_brand"] = normalize_str_list(normalized.get("preferred_brand"))
    normalized["budget_range"] = [int(budget_range[0]), int(budget_range[1])]
    normalized["interests"] = normalize_str_list(normalized.get("interests"))
    normalized["category"] = category
    normalized["preferred_categories"] = preferred_categories
    normalized["price_sensitivity"] = normalized.get("price_sensitivity") or "medium"
    normalized["scenario"] = normalized.get("scenario") or ""
    normalized["sort_preference"] = normalized.get("sort_preference") or "balanced"
    normalized["urgency"] = normalized.get("urgency") or "normal"
    normalized["fulfillment_preference"] = normalized.get("fulfillment_preference") or "standard"
    normalized["required_features"] = normalize_str_list(normalized.get("required_features"))
    return normalized


def parse_rule_based_intent(query: str) -> Dict:
    category = extract_category(query)
    sort_preference = extract_sort_preference(query)
    budget_range = extract_budget_range(query)
    interests = extract_interests(query)
    required_features = list(dict.fromkeys(extract_required_features(query) + interests))

    return {
        "preferred_brand": extract_brands(query),
        "budget_range": budget_range,
        "interests": interests,
        "category": category,
        "preferred_categories": [category] if category else [],
        "price_sensitivity": extract_price_sensitivity(query, budget_range, sort_preference),
        "scenario": extract_scenario(query),
        "sort_preference": sort_preference,
        "urgency": extract_urgency(query),
        "fulfillment_preference": extract_fulfillment_preference(query),
        "required_features": required_features,
    }
