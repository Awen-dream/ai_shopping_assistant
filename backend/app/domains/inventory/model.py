CITY_REGION_MAP = {
    "shanghai": "华东仓",
    "suzhou": "华东仓",
    "hangzhou": "华东仓",
    "beijing": "华北仓",
    "tianjin": "华北仓",
    "guangzhou": "华南仓",
    "shenzhen": "华南仓",
    "chengdu": "西南仓",
    "chongqing": "西南仓",
    "wuhan": "华中仓",
    "xian": "西北仓",
    "西安": "西北仓",
    "苏州": "华东仓",
    "上海": "华东仓",
    "北京": "华北仓",
    "广州": "华南仓",
    "深圳": "华南仓",
    "成都": "西南仓",
    "武汉": "华中仓",
}


def preferred_warehouse_name(user_profile: dict | None) -> str:
    city = (user_profile or {}).get("city", "")
    if not city:
        return ""
    city_lower = city.lower()
    return CITY_REGION_MAP.get(city, "") or CITY_REGION_MAP.get(city_lower, "")


def choose_warehouse(warehouses: list[dict], preferred_name: str, offset: int) -> dict | None:
    if not warehouses:
        return None
    if preferred_name:
        for warehouse in warehouses:
            if warehouse.get("name") == preferred_name and warehouse.get("stock", 0) > 0:
                return warehouse
    ordered = sorted(warehouses, key=lambda item: item.get("stock", 0), reverse=True)
    return ordered[offset % len(ordered)]


def purchase_limit(stock_count: int, promotion_tag: str) -> int:
    if stock_count <= 3:
        return 1
    if stock_count <= 10:
        return 2
    if promotion_tag and any(keyword in promotion_tag for keyword in ["国补", "教育", "限时"]):
        return 2
    return 5


def enrich_offer_with_inventory(
    product: dict,
    offer: dict,
    warehouses: list[dict],
    preferred_name: str,
    user_profile: dict | None,
    offset: int,
) -> dict:
    profile = user_profile or {}
    urgency = profile.get("urgency", "normal")
    fulfillment_preference = profile.get("fulfillment_preference", "standard")
    warehouse_total = sum(warehouse.get("stock", 0) for warehouse in warehouses)

    warehouse = choose_warehouse(warehouses, preferred_name, offset)
    warehouse_name = warehouse.get("name") if warehouse else "默认仓"
    warehouse_stock = warehouse.get("stock", 0) if warehouse else 0

    stock_count = max(0, warehouse_stock - offset * 2)
    shipping_days = offer.get("shipping_days", 0)
    if preferred_name and warehouse_name == preferred_name and stock_count > 0:
        shipping_days = max(1, shipping_days - 1)

    fulfillment_type = "现货"
    presale_days = 0
    if stock_count == 0 and warehouse_total > 0:
        stock_count = max(1, warehouse_total // max(len(warehouses), 1) - offset * 2)
        fulfillment_type = "调货"
        shipping_days += 2
    if stock_count <= 1 and (urgency != "urgent" or fulfillment_preference == "presale_ok"):
        fulfillment_type = "预售"
        presale_days = 3 if product.get("category") == "耳机" else 5
        shipping_days += presale_days

    stock_status = "现货"
    if fulfillment_type == "预售":
        stock_status = "预售中"
    elif stock_count <= 5:
        stock_status = "库存紧张"
    elif fulfillment_type == "调货":
        stock_status = "需调货"

    enriched_offer = offer.copy()
    enriched_offer["shipping_days"] = shipping_days
    enriched_offer["stock_count"] = stock_count
    enriched_offer["stock_status"] = stock_status
    enriched_offer["fulfillment_type"] = fulfillment_type
    enriched_offer["presale_days"] = presale_days
    enriched_offer["purchase_limit"] = purchase_limit(stock_count, product.get("promotion_tag", ""))
    enriched_offer["fulfillment_warehouse"] = warehouse_name
    enriched_offer["estimated_delivery"] = (
        f"{shipping_days} 天内发货" if fulfillment_type != "预售" else f"预计 {presale_days} 天后发货"
    )
    return enriched_offer


def apply_inventory_policy(products: list[dict], user_profile: dict | None = None) -> list[dict]:
    preferred_name = preferred_warehouse_name(user_profile)

    for product in products:
        warehouses = product.get("warehouses", [])
        available = [
            enrich_offer_with_inventory(product, offer, warehouses, preferred_name, user_profile, index)
            for index, offer in enumerate(product.get("search_results", []))
        ]
        available.sort(key=lambda item: (item.get("price_score", item["sale_price"]), item["shipping_days"]))
        product["search_results"] = available
        product["available"] = available
        product["best_offer"] = available[0] if available else None
    return products
