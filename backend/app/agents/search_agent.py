FAST_CITY_SET = {
    "shanghai",
    "hangzhou",
    "suzhou",
    "beijing",
    "guangzhou",
    "shenzhen",
    "上海",
    "杭州",
    "苏州",
    "北京",
    "广州",
    "深圳",
}


class SearchAgent:
    STORE_TEMPLATES = [
        {
            "channel": "official",
            "merchant_type": "official",
            "list_multiplier": 1.00,
            "sale_multiplier": 0.97,
            "promotion": "官方直降",
            "shipping_days": 2,
            "service_score": 4.9,
            "strategy_tags": ["官方保障", "售后稳定"],
        },
        {
            "channel": "jd",
            "merchant_type": "platform",
            "store": "JD Mall",
            "list_multiplier": 0.99,
            "sale_multiplier": 0.93,
            "promotion": "券后价",
            "shipping_days": 2,
            "service_score": 4.8,
            "strategy_tags": ["价格竞争力", "物流稳定"],
        },
        {
            "channel": "tmall",
            "merchant_type": "platform",
            "store": "Tmall",
            "list_multiplier": 1.01,
            "sale_multiplier": 0.94,
            "promotion": "满减后",
            "shipping_days": 3,
            "service_score": 4.7,
            "strategy_tags": ["活动频繁", "店铺选择多"],
        },
    ]

    @staticmethod
    def _city_is_fast_lane(user_profile):
        city = (user_profile or {}).get("city", "")
        return city.lower() in FAST_CITY_SET or city in FAST_CITY_SET

    @staticmethod
    def _official_store_name(product):
        brand = product.get("brand") or "Brand"
        return f"{brand} Official"

    @classmethod
    def _strategy_adjustments(cls, product, template, user_profile):
        user_profile = user_profile or {}
        scenario = user_profile.get("scenario", "")
        urgency = user_profile.get("urgency", "normal")
        sort_preference = user_profile.get("sort_preference", "balanced")

        sale_multiplier = template["sale_multiplier"]
        shipping_days = template["shipping_days"]
        strategy_tags = list(template["strategy_tags"])

        if product.get("promotion_tag"):
            sale_multiplier -= 0.01
            strategy_tags.append("活动商品")

        if product.get("category") == "笔记本" and template["channel"] in {"jd", "tmall"}:
            sale_multiplier -= 0.005
        if product.get("category") == "耳机" and template["channel"] == "jd":
            shipping_days -= 1
        if product.get("category") == "手机" and template["channel"] == "official":
            strategy_tags.append("新品优先")

        if scenario == "学生" and product.get("category") == "笔记本" and template["channel"] in {"jd", "tmall"}:
            sale_multiplier -= 0.01
            strategy_tags.append("学生友好")
        if scenario == "商务" and template["channel"] == "official":
            shipping_days -= 1
            strategy_tags.append("商务保障")
        if scenario == "通勤" and template["channel"] == "jd":
            shipping_days -= 1
            strategy_tags.append("通勤快送")

        if sort_preference == "price" and template["channel"] != "official":
            sale_multiplier -= 0.005
        if urgency == "urgent" and template["channel"] == "jd":
            shipping_days -= 1
            strategy_tags.append("急速履约")
        if cls._city_is_fast_lane(user_profile) and template["channel"] in {"jd", "official"}:
            shipping_days -= 1
            strategy_tags.append("核心城市覆盖")

        return max(sale_multiplier, 0.84), max(shipping_days, 1), list(dict.fromkeys(strategy_tags))

    def search(self, products, user_profile=None):
        for product in products:
            base_price = product["price"]
            search_results = []

            for template in self.STORE_TEMPLATES:
                sale_multiplier, shipping_days, strategy_tags = self._strategy_adjustments(
                    product,
                    template,
                    user_profile,
                )
                store_name = template.get("store") or self._official_store_name(product)
                list_price = round(base_price * template["list_multiplier"], 2)
                sale_price = round(base_price * sale_multiplier, 2)

                search_results.append({
                    "store": store_name,
                    "channel": template["channel"],
                    "merchant_type": template["merchant_type"],
                    "product_id": product["id"],
                    "list_price": list_price,
                    "sale_price": sale_price,
                    "discount": round(list_price - sale_price, 2),
                    "promotion": template["promotion"],
                    "shipping_days": shipping_days,
                    "currency": "CNY",
                    "service_score": template["service_score"],
                    "strategy_tags": strategy_tags,
                })

            product["search_results"] = search_results
        return products
