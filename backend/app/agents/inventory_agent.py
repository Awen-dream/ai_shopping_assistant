class InventoryAgent:
    def filter_stock(self, products):
        for p in products:
            available = []
            warehouse_total = sum(warehouse.get("stock", 0) for warehouse in p.get("warehouses", []))
            for index, item in enumerate(p["search_results"]):
                stock_count = max(1, warehouse_total // max(len(p["search_results"]), 1) - index * 2)
                enriched_item = item.copy()
                enriched_item["stock_count"] = stock_count
                enriched_item["stock_status"] = "现货" if stock_count > 8 else "库存紧张"
                available.append(enriched_item)

            p["search_results"] = available
            p["available"] = available
            p["best_offer"] = available[0] if available else None
        return products
