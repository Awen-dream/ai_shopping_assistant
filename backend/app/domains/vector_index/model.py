def build_product_text(product: dict) -> str:
    fields = [
        product.get("name", ""),
        product.get("description", ""),
        product.get("category", ""),
        product.get("subcategory", ""),
        product.get("brand", ""),
        " ".join(product.get("tags", [])),
        product.get("promotion_tag", ""),
    ]
    return " ".join(part for part in fields if part)
