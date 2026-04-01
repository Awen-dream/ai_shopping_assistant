from ...agents.price_agent import PriceAgent
from ..pipeline import normalize_pipeline_products
from .model import compare_product_prices


def create_price_agent():
    return PriceAgent()


def compare_prices(products, user_profile: dict | None = None):
    return normalize_pipeline_products(
        compare_product_prices(products, user_profile=user_profile),
        stage="priced",
    )
