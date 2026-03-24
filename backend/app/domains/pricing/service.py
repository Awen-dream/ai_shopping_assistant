from ...agents.price_agent import PriceAgent


def create_price_agent():
    return PriceAgent()


def compare_prices(products, user_profile: dict | None = None):
    return create_price_agent().compare(products, user_profile=user_profile)
