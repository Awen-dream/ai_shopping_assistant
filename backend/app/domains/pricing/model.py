PROMOTION_DISCOUNT_MAP = {
    "教育优惠": 0.05,
    "国补专区": 0.06,
    "以旧换新补贴": 0.04,
    "限时满减": 0.03,
    "企业采购优惠": 0.03,
    "直降": 0.03,
    "赠延保服务": 0.01,
}


def promotion_discount_ratio(product: dict, offer: dict, user_profile: dict | None) -> float:
    promotion_tag = product.get("promotion_tag", "")
    ratio = 0.0
    for keyword, discount_ratio in PROMOTION_DISCOUNT_MAP.items():
        if keyword in promotion_tag:
            ratio = max(ratio, discount_ratio)

    profile = user_profile or {}
    scenario = profile.get("scenario", "")
    sort_preference = profile.get("sort_preference", "balanced")
    price_sensitivity = profile.get("price_sensitivity", "medium")

    if scenario == "学生" and ("教育优惠" in promotion_tag or product.get("brand") in {"Lenovo", "Apple"}):
        ratio += 0.015
    if sort_preference == "price":
        ratio += 0.01
    if price_sensitivity == "high":
        ratio += 0.015
    elif price_sensitivity == "low" and offer.get("merchant_type") == "official":
        ratio += 0.005

    if offer.get("channel") == "jd" and product.get("category") in {"手机", "耳机"}:
        ratio += 0.005
    if offer.get("channel") == "tmall" and product.get("brand") in {"Lenovo", "Xiaomi"}:
        ratio += 0.005

    return min(ratio, 0.12)


def price_label(final_price: float, base_price: float) -> str:
    savings_ratio = 1 - (final_price / max(base_price, 1))
    if savings_ratio >= 0.12:
        return "大促低价"
    if savings_ratio >= 0.07:
        return "活动好价"
    return "日常价"


def enrich_offer_with_pricing(product: dict, offer: dict, user_profile: dict | None) -> dict:
    profile = user_profile or {}
    urgency = profile.get("urgency", "normal")
    base_price = product.get("price", 0)
    enriched_offer = offer.copy()

    discount_ratio = promotion_discount_ratio(product, offer, profile)
    coupon_discount = round(offer["sale_price"] * discount_ratio, 2)
    final_price = round(max(offer["sale_price"] - coupon_discount, offer["sale_price"] * 0.82), 2)

    promotion_applied = []
    if product.get("promotion_tag"):
        promotion_applied.append(product["promotion_tag"])
    if discount_ratio > 0:
        promotion_applied.append("智能折扣策略")
    if profile.get("scenario") == "学生" and "教育优惠" in product.get("promotion_tag", ""):
        promotion_applied.append("学生场景加码")

    shipping_penalty = offer.get("shipping_days", 0) * 30 if urgency == "urgent" else 0

    enriched_offer["coupon_discount"] = coupon_discount
    enriched_offer["dynamic_discount_ratio"] = round(discount_ratio, 4)
    enriched_offer["promotion_applied"] = promotion_applied
    enriched_offer["final_price"] = final_price
    enriched_offer["sale_price"] = final_price
    enriched_offer["discount"] = round(enriched_offer["list_price"] - final_price, 2)
    enriched_offer["price_label"] = price_label(final_price, base_price)
    enriched_offer["price_score"] = round(final_price + shipping_penalty, 2)
    return enriched_offer


def compare_product_prices(products: list[dict], user_profile: dict | None = None) -> list[dict]:
    for product in products:
        priced_results = [
            enrich_offer_with_pricing(product, offer, user_profile)
            for offer in product.get("search_results", [])
        ]
        sorted_results = sorted(
            priced_results,
            key=lambda item: (
                item["price_score"],
                item["shipping_days"],
                -item.get("service_score", 0),
                item["store"],
            ),
        )
        product["search_results"] = sorted_results
        product["best_offer"] = sorted_results[0] if sorted_results else None
    return products
