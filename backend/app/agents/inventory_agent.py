from app.domains.inventory.model import apply_inventory_policy


class InventoryAgent:
    def filter_stock(self, products, user_profile=None):
        return apply_inventory_policy(products, user_profile=user_profile)
