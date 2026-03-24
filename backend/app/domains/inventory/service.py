from ...agents.inventory_agent import InventoryAgent


def create_inventory_agent():
    return InventoryAgent()


def apply_inventory_rules(products, user_profile: dict | None = None):
    return create_inventory_agent().filter_stock(products, user_profile=user_profile)
