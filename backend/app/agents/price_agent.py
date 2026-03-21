class PriceAgent:
    def compare(self, products):
        for p in products:
            sorted_results = sorted(
                p["search_results"],
                key=lambda item: (item["sale_price"], item["shipping_days"])
            )
            p["search_results"] = sorted_results
            p["best_offer"] = sorted_results[0] if sorted_results else None
        return products
