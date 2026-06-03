from __future__ import annotations

from catalog_seed import DEFAULT_CATEGORIES, DEFAULT_PRODUCT_TYPES, DEFAULT_PRODUCTS


FALLBACK_PRODUCTS = [
    {
        "id": index,
        "title": product["name"],
        "price": product["price"],
        "stock_quantity": product["stock_quantity"],
        "category_id": index,
        "category_name": category["name"],
        "product_type_name": product_type["name"],
        "description": product["description"],
        "attributes": product["attributes"],
    }
    for index, (product, category, product_type) in enumerate(
        zip(DEFAULT_PRODUCTS, DEFAULT_CATEGORIES, DEFAULT_PRODUCT_TYPES),
        start=1,
    )
]

FALLBACK_CATEGORIES = [
    {"id": index, "name": category["name"]}
    for index, category in enumerate(DEFAULT_CATEGORIES, start=1)
]

FALLBACK_PROMOTIONS = [
    {
        "name": "Mùa tựu trường",
        "description": "Giảm giá cho sách, dụng cụ học tập và phụ kiện đi học.",
        "discount_percent": 10,
        "is_active": True,
    }
]

FALLBACK_COUPONS = [{"code": "SALE20", "discount_percent": 20, "min_order_value": 100000, "active": True}]

FALLBACK_TIERS = [
    {"name": "Bronze", "min_points": 0, "discount_percent": 0, "free_shipping": False},
    {"name": "Silver", "min_points": 500, "discount_percent": 3, "free_shipping": False},
    {"name": "Gold", "min_points": 2000, "discount_percent": 5, "free_shipping": True},
    {"name": "Platinum", "min_points": 5000, "discount_percent": 10, "free_shipping": True},
]
