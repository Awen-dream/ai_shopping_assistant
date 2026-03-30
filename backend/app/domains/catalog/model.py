from copy import deepcopy


DEFAULT_PRODUCT = {
    "name": "",
    "description": "",
    "category": "",
    "subcategory": "",
    "brand": "",
    "price": 0,
    "rating": 0,
    "tags": [],
    "feature_highlights": [],
    "use_cases": [],
    "target_users": [],
    "monthly_sales": 0,
    "promotion_tag": "",
    "inventory_total": 0,
    "warehouses": [],
}


def normalize_product(product_id: int, payload: dict | None) -> dict:
    normalized = deepcopy(DEFAULT_PRODUCT)
    if payload:
        normalized.update(payload)

    tags = normalized.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    feature_highlights = normalized.get("feature_highlights") or []
    if isinstance(feature_highlights, str):
        feature_highlights = [feature_highlights]
    use_cases = normalized.get("use_cases") or []
    if isinstance(use_cases, str):
        use_cases = [use_cases]
    target_users = normalized.get("target_users") or []
    if isinstance(target_users, str):
        target_users = [target_users]

    warehouses = normalized.get("warehouses") or []
    normalized_warehouses = []
    for warehouse in warehouses:
        if not isinstance(warehouse, dict):
            continue
        normalized_warehouses.append(
            {
                "name": warehouse.get("name", ""),
                "stock": int(warehouse.get("stock", 0)),
            }
        )

    normalized["id"] = int(product_id)
    normalized["name"] = normalized.get("name", "")
    normalized["description"] = normalized.get("description", "")
    normalized["category"] = normalized.get("category", "")
    normalized["subcategory"] = normalized.get("subcategory", "")
    normalized["brand"] = normalized.get("brand", "")
    normalized["price"] = float(normalized.get("price", 0))
    normalized["rating"] = float(normalized.get("rating", 0))
    normalized["tags"] = tags
    normalized["feature_highlights"] = [str(item) for item in feature_highlights if item]
    normalized["use_cases"] = [str(item) for item in use_cases if item]
    normalized["target_users"] = [str(item) for item in target_users if item]
    normalized["monthly_sales"] = int(normalized.get("monthly_sales", 0))
    normalized["promotion_tag"] = normalized.get("promotion_tag", "")
    normalized["inventory_total"] = int(normalized.get("inventory_total", 0))

    if not normalized_warehouses and normalized["inventory_total"] > 0:
        normalized_warehouses = [{"name": "默认仓", "stock": normalized["inventory_total"]}]
    if normalized["inventory_total"] <= 0 and normalized_warehouses:
        normalized["inventory_total"] = sum(warehouse["stock"] for warehouse in normalized_warehouses)

    normalized["warehouses"] = normalized_warehouses
    return normalized
