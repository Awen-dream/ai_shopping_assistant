import json

def get_product_by_id(product_id: int):
    with open("backend/data/products.json") as f:
        products = json.load(f)
    for p in products:
        if p["id"] == product_id:
            return p
    return None

def list_products():
    with open("backend/data/products.json") as f:
        return json.load(f)