from pydantic import BaseModel


class UserProfilePayload(BaseModel):
    preferred_brand: list[str] | None = None
    favorite_brands: list[str] | None = None
    budget_range: list[int] | None = None
    interests: list[str] | None = None
    category: str | None = None
    preferred_categories: list[str] | None = None
    recent_categories: list[str] | None = None
    recent_clicked_product_ids: list[int] | None = None
    price_sensitivity: str | None = None
    price_band_preference: str | None = None
    city: str | None = None


class WarehousePayload(BaseModel):
    name: str
    stock: int


class ProductPayload(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    subcategory: str | None = None
    brand: str | None = None
    price: float | None = None
    rating: float | None = None
    tags: list[str] | None = None
    feature_highlights: list[str] | None = None
    use_cases: list[str] | None = None
    target_users: list[str] | None = None
    monthly_sales: int | None = None
    promotion_tag: str | None = None
    inventory_total: int | None = None
    warehouses: list[WarehousePayload] | None = None


class FeedbackPayload(BaseModel):
    event_type: str
    product_id: int
    product_name: str | None = None
    query: str | None = None
    user_id: str | None = None
