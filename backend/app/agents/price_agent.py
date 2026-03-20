class PriceAgent:
    def compare(self, products):
        for p in products:
            # 模拟价格比较
            for item in p["search_results"]:
                item["price"] = p["price"] * (0.9 if item["store"] == "StoreA" else 1.1)
        return products