class InventoryAgent:
    def filter_stock(self, products):
        for p in products:
            # 模拟库存过滤
            p["available"] = [item for item in p["search_results"] if item["price"] > 0]
        return products