class SearchAgent:
    def search(self, products):
        # 模拟搜索，多商家结果
        for p in products:
            p["search_results"] = [
                {"store": "StoreA", "id": p["id"]},
                {"store": "StoreB", "id": p["id"]}
            ]
        return products