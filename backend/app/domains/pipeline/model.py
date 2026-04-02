from dataclasses import dataclass, field
from typing import Any


PIPELINE_CONTRACT_VERSION = "stage3.v1"


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _as_int_list(value: Any, default: list[int]) -> list[int]:
    values = _as_list(value)
    if not values:
        return list(default)
    normalized = []
    for item in values:
        try:
            normalized.append(int(item))
        except (TypeError, ValueError):
            continue
    return normalized or list(default)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class QueryIntentContract:
    raw_query: str = ""
    category: str = ""
    preferred_brand: list[str] = field(default_factory=list)
    favorite_brands: list[str] = field(default_factory=list)
    budget_range: list[int] = field(default_factory=lambda: [0, 999999])
    interests: list[str] = field(default_factory=list)
    required_features: list[str] = field(default_factory=list)
    preferred_categories: list[str] = field(default_factory=list)
    recent_categories: list[str] = field(default_factory=list)
    recent_clicked_product_ids: list[int] = field(default_factory=list)
    price_sensitivity: str = "medium"
    price_band_preference: str = "flexible"
    scenario: str = ""
    sort_preference: str = "balanced"
    urgency: str = "normal"
    fulfillment_preference: str = "standard"
    city: str = ""
    merchant_preference: str = ""
    quality_preference: str = ""
    intent_confidence: float = 0.0
    conflict_flags: list[str] = field(default_factory=list)

    @classmethod
    def from_profile(cls, profile: dict | None, raw_query: str = "") -> "QueryIntentContract":
        profile = profile or {}
        return cls(
            raw_query=raw_query,
            category=str(profile.get("category") or ""),
            preferred_brand=[str(item) for item in _as_list(profile.get("preferred_brand")) if item],
            favorite_brands=[str(item) for item in _as_list(profile.get("favorite_brands")) if item],
            budget_range=_as_int_list(profile.get("budget_range"), [0, 999999]),
            interests=[str(item) for item in _as_list(profile.get("interests")) if item],
            required_features=[str(item) for item in _as_list(profile.get("required_features")) if item],
            preferred_categories=[str(item) for item in _as_list(profile.get("preferred_categories")) if item],
            recent_categories=[str(item) for item in _as_list(profile.get("recent_categories")) if item],
            recent_clicked_product_ids=_as_int_list(profile.get("recent_clicked_product_ids"), []),
            price_sensitivity=str(profile.get("price_sensitivity") or "medium"),
            price_band_preference=str(profile.get("price_band_preference") or "flexible"),
            scenario=str(profile.get("scenario") or ""),
            sort_preference=str(profile.get("sort_preference") or "balanced"),
            urgency=str(profile.get("urgency") or "normal"),
            fulfillment_preference=str(profile.get("fulfillment_preference") or "standard"),
            city=str(profile.get("city") or ""),
            merchant_preference=str(profile.get("merchant_preference") or ""),
            quality_preference=str(profile.get("quality_preference") or ""),
            intent_confidence=_as_float(profile.get("intent_confidence"), 0.0),
            conflict_flags=[str(item) for item in _as_list(profile.get("conflict_flags")) if item],
        )

    def to_profile(self) -> dict:
        return {
            "raw_query": self.raw_query,
            "category": self.category,
            "preferred_brand": list(self.preferred_brand),
            "favorite_brands": list(self.favorite_brands),
            "budget_range": list(self.budget_range),
            "interests": list(self.interests),
            "required_features": list(self.required_features),
            "preferred_categories": list(self.preferred_categories),
            "recent_categories": list(self.recent_categories),
            "recent_clicked_product_ids": list(self.recent_clicked_product_ids),
            "price_sensitivity": self.price_sensitivity,
            "price_band_preference": self.price_band_preference,
            "scenario": self.scenario,
            "sort_preference": self.sort_preference,
            "urgency": self.urgency,
            "fulfillment_preference": self.fulfillment_preference,
            "city": self.city,
            "merchant_preference": self.merchant_preference,
            "quality_preference": self.quality_preference,
            "intent_confidence": self.intent_confidence,
            "conflict_flags": list(self.conflict_flags),
        }


@dataclass
class OfferContract:
    store: str = ""
    channel: str = ""
    merchant_type: str = ""
    product_id: int | None = None
    list_price: float = 0.0
    sale_price: float = 0.0
    discount: float = 0.0
    promotion: str = ""
    shipping_days: int = 0
    currency: str = "CNY"
    service_score: float = 0.0
    strategy_tags: list[str] = field(default_factory=list)
    coupon_discount: float = 0.0
    dynamic_discount_ratio: float = 0.0
    promotion_applied: list[str] = field(default_factory=list)
    final_price: float = 0.0
    price_label: str = ""
    price_score: float = 0.0
    stock_count: int = 0
    stock_status: str = ""
    fulfillment_type: str = ""
    presale_days: int = 0
    purchase_limit: int = 0
    fulfillment_warehouse: str = ""
    estimated_delivery: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict | None) -> "OfferContract":
        payload = data or {}
        known_keys = {
            "store",
            "channel",
            "merchant_type",
            "product_id",
            "list_price",
            "sale_price",
            "discount",
            "promotion",
            "shipping_days",
            "currency",
            "service_score",
            "strategy_tags",
            "coupon_discount",
            "dynamic_discount_ratio",
            "promotion_applied",
            "final_price",
            "price_label",
            "price_score",
            "stock_count",
            "stock_status",
            "fulfillment_type",
            "presale_days",
            "purchase_limit",
            "fulfillment_warehouse",
            "estimated_delivery",
        }
        extras = {key: value for key, value in payload.items() if key not in known_keys}
        return cls(
            store=str(payload.get("store") or ""),
            channel=str(payload.get("channel") or ""),
            merchant_type=str(payload.get("merchant_type") or ""),
            product_id=payload.get("product_id"),
            list_price=_as_float(payload.get("list_price")),
            sale_price=_as_float(payload.get("sale_price")),
            discount=_as_float(payload.get("discount")),
            promotion=str(payload.get("promotion") or ""),
            shipping_days=_as_int(payload.get("shipping_days")),
            currency=str(payload.get("currency") or "CNY"),
            service_score=_as_float(payload.get("service_score")),
            strategy_tags=[str(item) for item in _as_list(payload.get("strategy_tags")) if item],
            coupon_discount=_as_float(payload.get("coupon_discount")),
            dynamic_discount_ratio=_as_float(payload.get("dynamic_discount_ratio")),
            promotion_applied=[str(item) for item in _as_list(payload.get("promotion_applied")) if item],
            final_price=_as_float(payload.get("final_price")),
            price_label=str(payload.get("price_label") or ""),
            price_score=_as_float(payload.get("price_score")),
            stock_count=_as_int(payload.get("stock_count")),
            stock_status=str(payload.get("stock_status") or ""),
            fulfillment_type=str(payload.get("fulfillment_type") or ""),
            presale_days=_as_int(payload.get("presale_days")),
            purchase_limit=_as_int(payload.get("purchase_limit")),
            fulfillment_warehouse=str(payload.get("fulfillment_warehouse") or ""),
            estimated_delivery=str(payload.get("estimated_delivery") or ""),
            extras=extras,
        )

    def to_dict(self) -> dict:
        payload = {
            "store": self.store,
            "channel": self.channel,
            "merchant_type": self.merchant_type,
            "product_id": self.product_id,
            "list_price": self.list_price,
            "sale_price": self.sale_price,
            "discount": self.discount,
            "promotion": self.promotion,
            "shipping_days": self.shipping_days,
            "currency": self.currency,
            "service_score": self.service_score,
            "strategy_tags": list(self.strategy_tags),
            "coupon_discount": self.coupon_discount,
            "dynamic_discount_ratio": self.dynamic_discount_ratio,
            "promotion_applied": list(self.promotion_applied),
            "final_price": self.final_price,
            "price_label": self.price_label,
            "price_score": self.price_score,
            "stock_count": self.stock_count,
            "stock_status": self.stock_status,
            "fulfillment_type": self.fulfillment_type,
            "presale_days": self.presale_days,
            "purchase_limit": self.purchase_limit,
            "fulfillment_warehouse": self.fulfillment_warehouse,
            "estimated_delivery": self.estimated_delivery,
        }
        payload.update(self.extras)
        return payload


@dataclass
class ProductResultContract:
    id: int | None = None
    name: str = ""
    brand: str = ""
    category: str = ""
    subcategory: str = ""
    rating: float = 0.0
    price: float = 0.0
    monthly_sales: int = 0
    promotion_tag: str = ""
    inventory_total: int = 0
    reason: str = ""
    match_score: float = 0.0
    matched_features: dict[str, Any] = field(default_factory=dict)
    best_offer: OfferContract | None = None
    available: list[OfferContract] = field(default_factory=list)
    search_results: list[OfferContract] = field(default_factory=list)
    pipeline: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict | None, stage: str = "") -> "ProductResultContract":
        payload = data or {}
        known_keys = {
            "id",
            "name",
            "brand",
            "category",
            "subcategory",
            "rating",
            "price",
            "monthly_sales",
            "promotion_tag",
            "inventory_total",
            "reason",
            "match_score",
            "matched_features",
            "best_offer",
            "available",
            "search_results",
            "pipeline",
        }
        pipeline = payload.get("pipeline") or {}
        if stage:
            pipeline = {
                **pipeline,
                "contract_version": PIPELINE_CONTRACT_VERSION,
                "stage": stage,
            }
        else:
            pipeline = {
                **pipeline,
                "contract_version": pipeline.get("contract_version") or PIPELINE_CONTRACT_VERSION,
                "stage": pipeline.get("stage") or "",
            }
        extras = {key: value for key, value in payload.items() if key not in known_keys}
        return cls(
            id=payload.get("id"),
            name=str(payload.get("name") or ""),
            brand=str(payload.get("brand") or ""),
            category=str(payload.get("category") or ""),
            subcategory=str(payload.get("subcategory") or ""),
            rating=_as_float(payload.get("rating")),
            price=_as_float(payload.get("price")),
            monthly_sales=_as_int(payload.get("monthly_sales")),
            promotion_tag=str(payload.get("promotion_tag") or ""),
            inventory_total=_as_int(payload.get("inventory_total")),
            reason=str(payload.get("reason") or ""),
            match_score=_as_float(payload.get("match_score")),
            matched_features=dict(payload.get("matched_features") or {}),
            best_offer=OfferContract.from_dict(payload.get("best_offer")) if payload.get("best_offer") else None,
            available=[OfferContract.from_dict(item) for item in _as_list(payload.get("available"))],
            search_results=[OfferContract.from_dict(item) for item in _as_list(payload.get("search_results"))],
            pipeline=pipeline,
            extras=extras,
        )

    def to_dict(self) -> dict:
        payload = {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "subcategory": self.subcategory,
            "rating": self.rating,
            "price": self.price,
            "monthly_sales": self.monthly_sales,
            "promotion_tag": self.promotion_tag,
            "inventory_total": self.inventory_total,
            "reason": self.reason,
            "match_score": self.match_score,
            "matched_features": self.matched_features,
            "best_offer": self.best_offer.to_dict() if self.best_offer else None,
            "available": [offer.to_dict() for offer in self.available],
            "search_results": [offer.to_dict() for offer in self.search_results],
            "pipeline": {
                "contract_version": self.pipeline.get("contract_version") or PIPELINE_CONTRACT_VERSION,
                "stage": self.pipeline.get("stage") or "",
            },
        }
        payload.update(self.extras)
        return payload


def normalize_intent_profile(profile: dict | None, raw_query: str = "") -> dict:
    return QueryIntentContract.from_profile(profile, raw_query=raw_query).to_profile()


def normalize_pipeline_products(products: list[dict] | None, stage: str) -> list[dict]:
    return [ProductResultContract.from_dict(item, stage=stage).to_dict() for item in products or []]


def build_safe_product_payload(product: dict | None) -> dict:
    contract = ProductResultContract.from_dict(product)
    payload = contract.to_dict()
    return {
        "id": payload.get("id"),
        "name": payload.get("name"),
        "brand": payload.get("brand"),
        "category": payload.get("category"),
        "subcategory": payload.get("subcategory"),
        "rating": payload.get("rating"),
        "price": payload.get("price"),
        "monthly_sales": payload.get("monthly_sales"),
        "promotion_tag": payload.get("promotion_tag"),
        "inventory_total": payload.get("inventory_total"),
        "reason": payload.get("reason", ""),
        "match_score": payload.get("match_score"),
        "matched_features": payload.get("matched_features", {}),
        "best_offer": payload.get("best_offer"),
        "available": payload.get("available", []),
        "search_results": payload.get("search_results", []),
        "pipeline": payload.get("pipeline", {}),
    }
