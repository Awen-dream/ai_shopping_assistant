class InventoryAgent:
    def filter_stock(self, products):
        for p in products:
            available = []
            for index, item in enumerate(p["search_results"]):
                stock_count = max(1, 12 - (p["id"] * 2 + index * 3))
                enriched_item = item.copy()
                enriched_item["stock_count"] = stock_count
                enriched_item["stock_status"] = "现货" if stock_count > 3 else "库存紧张"
                available.append(enriched_item)

            p["search_results"] = available
            p["available"] = available
            p["best_offer"] = available[0] if available else None
        return products
