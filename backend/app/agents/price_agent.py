from app.domains.pricing.model import compare_product_prices


class PriceAgent:
    def compare(self, products, user_profile=None):
        return compare_product_prices(products, user_profile=user_profile)
