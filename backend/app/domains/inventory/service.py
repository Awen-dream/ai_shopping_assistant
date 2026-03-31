from ...agents.inventory_agent import InventoryAgent
from .model import apply_inventory_policy


def create_inventory_agent():
    return InventoryAgent()


def apply_inventory_rules(products, user_profile: dict | None = None):
    return apply_inventory_policy(products, user_profile=user_profile)
