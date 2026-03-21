class SearchAgent:
    def search(self, products):
        store_rules = [
            {"store": "Apple/Sony Official", "list_multiplier": 1.00, "sale_multiplier": 0.97, "promotion": "官方直降", "shipping_days": 1},
            {"store": "JD Mall", "list_multiplier": 0.99, "sale_multiplier": 0.93, "promotion": "券后价", "shipping_days": 2},
            {"store": "Tmall", "list_multiplier": 1.02, "sale_multiplier": 0.95, "promotion": "满减后", "shipping_days": 2},
        ]

        for p in products:
            base_price = p["price"]
            p["search_results"] = []
            for rule in store_rules:
                promotion_boost = 0.01 if p.get("promotion_tag") else 0.0
                list_price = round(base_price * rule["list_multiplier"], 2)
                sale_price = round(base_price * max(rule["sale_multiplier"] - promotion_boost, 0.85), 2)
                p["search_results"].append({
                    "store": rule["store"],
                    "product_id": p["id"],
                    "list_price": list_price,
                    "sale_price": sale_price,
                    "discount": round(list_price - sale_price, 2),
                    "promotion": rule["promotion"],
                    "shipping_days": rule["shipping_days"],
                    "currency": "CNY",
                })
        return products
