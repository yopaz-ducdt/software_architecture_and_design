from __future__ import annotations

import os
from collections import Counter
from typing import Any

import httpx

from fixtures import FALLBACK_CATEGORIES, FALLBACK_COUPONS, FALLBACK_PRODUCTS, FALLBACK_PROMOTIONS, FALLBACK_TIERS


def _normalize_search_text(value: str) -> str:
    return " ".join((value or "").lower().split())


class ServiceClient:
    def __init__(self) -> None:
        self.timeout = float(os.getenv("AI_HTTP_TIMEOUT", "5.0"))
        self.product_url = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")
        self.order_url = os.getenv("ORDER_SERVICE_URL", "http://localhost:8003")
        self.customer_url = os.getenv("CUSTOMER_SERVICE_URL", "http://localhost:8004")
        self.analytics_url = os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8010")
        self.marketing_url = os.getenv("MARKETING_SERVICE_URL", "http://localhost:8006")
        self.behavior_url = os.getenv("BEHAVIOR_SERVICE_URL", "http://localhost:8013")

    def _get_json(self, url: str, default: Any) -> Any:
        try:
            with httpx.Client(timeout=httpx.Timeout(self.timeout, connect=self.timeout)) as client:
                response = client.get(url)
                if response.is_success:
                    return response.json()
        except Exception:
            pass
        return default

    def _safe_order_items(self, order_id: int) -> list[dict]:
        return self._get_json(f"{self.order_url}/orders/{order_id}/items", [])

    def get_products(self) -> list[dict]:
        return self._get_json(f"{self.product_url}/products?limit=200", FALLBACK_PRODUCTS) or FALLBACK_PRODUCTS

    def get_categories(self) -> list[dict]:
        return self._get_json(f"{self.product_url}/categories", FALLBACK_CATEGORIES) or FALLBACK_CATEGORIES

    def get_marketing_context(self) -> dict:
        return {
            "promotions": self._get_json(f"{self.marketing_url}/promotions", FALLBACK_PROMOTIONS) or FALLBACK_PROMOTIONS,
            "coupons": self._get_json(f"{self.marketing_url}/coupons", FALLBACK_COUPONS) or FALLBACK_COUPONS,
            "tiers": self._get_json(f"{self.marketing_url}/tiers", FALLBACK_TIERS) or FALLBACK_TIERS,
            "flash_sales": self._get_json(f"{self.marketing_url}/flash-sales", []),
        }

    def get_behavior_context(self, customer_id: int) -> dict:
        return self._get_json(
            f"{self.behavior_url}/features/{customer_id}",
            {
                "customer_id": customer_id,
                "preferred_categories": [],
                "feature_values": {},
                "persona": "new_explorer",
                "price_sensitivity": "medium",
                "purchase_intent": 0.1,
                "next_best_action": "recommend_entry_products",
            },
        )

    def get_user_snapshot(self, customer_id: int) -> dict:
        products = self.get_products()
        categories = self.get_categories()
        product_map = {p["id"]: p for p in products if isinstance(p, dict) and p.get("id") is not None}
        category_map = {c["id"]: c.get("name", str(c.get("id"))) for c in categories if isinstance(c, dict)}
        profile = self._get_json(f"{self.customer_url}/profile/{customer_id}", None)
        wishlist = self._get_json(f"{self.customer_url}/wishlist/{customer_id}", {"items": []})
        cart_summary = self._get_json(f"{self.order_url}/cart/{customer_id}/summary", {"item_count": 0})
        cart = self._get_json(f"{self.order_url}/cart/{customer_id}", {"items": []})
        orders = self._get_json(f"{self.order_url}/orders/customer/{customer_id}", [])
        searches = self._get_json(f"{self.analytics_url}/search-history?limit=200", [])
        searches = [item for item in searches if item.get("customer_id") == customer_id]
        recent_views = self._get_json(f"{self.analytics_url}/recently-viewed/{customer_id}?limit=20", [])
        behavior = self.get_behavior_context(customer_id)

        order_items: list[dict] = []
        for order in orders[:10]:
            order_id = order.get("id")
            if order_id:
                order_items.extend(self._safe_order_items(order_id))

        category_counter: Counter[str] = Counter()
        for viewed in recent_views:
            product = product_map.get(viewed.get("product_id") or viewed.get("book_id"))
            if product and product.get("category_id") in category_map:
                category_counter[category_map[product["category_id"]]] += 2
        for item in wishlist.get("items", []):
            product = product_map.get(item.get("product_id") or item.get("book_id"))
            if product and product.get("category_id") in category_map:
                category_counter[category_map[product["category_id"]]] += 2
        for item in order_items:
            product = product_map.get(item.get("product_id") or item.get("book_id"))
            if product and product.get("category_id") in category_map:
                category_counter[category_map[product["category_id"]]] += max(1, int(item.get("quantity", 1)))

        total_spent = float(sum(order.get("total_price", 0) or 0 for order in orders))
        avg_order_value = total_spent / len(orders) if orders else 0.0
        promo_keywords = 0
        recent_search_terms: list[str] = []
        viewed_product_ids: list[int] = []
        view_category_counter: Counter[str] = Counter()

        for item in searches:
            query = _normalize_search_text(item.get("query") or item.get("search_term") or "")
            if query:
                recent_search_terms.append(query)
            if any(keyword in query for keyword in ["sale", "giảm", "voucher", "coupon", "khuyến mãi"]):
                promo_keywords += 1

        for viewed in recent_views:
            product_id = viewed.get("product_id") or viewed.get("book_id")
            if product_id:
                viewed_product_ids.append(product_id)
            product = product_map.get(product_id)
            if product and product.get("category_id") in category_map:
                view_category_counter[category_map[product["category_id"]]] += 1

        preferred_categories = behavior.get("preferred_categories") or [name for name, _ in category_counter.most_common(3)]
        feature_values = {
            "search_count": len(searches),
            "view_count": len(recent_views),
            "wishlist_count": len(wishlist.get("items", [])),
            "cart_item_count": int(cart_summary.get("item_count", 0) or 0),
            "order_count": len(orders),
            "avg_order_value": round(avg_order_value, 2),
            "total_spent": round(total_spent, 2),
            "promo_keyword_count": promo_keywords,
            "membership_points": int((profile or {}).get("points", 0) or 0),
            "preferred_genre_count": len(preferred_categories),
        }
        feature_values.update(behavior.get("feature_values") or {})

        return {
            "customer_id": customer_id,
            "profile": profile,
            "wishlist": wishlist,
            "orders": orders,
            "searches": searches,
            "recent_views": recent_views,
            "products": products,
            "categories": categories,
            "marketing": self.get_marketing_context(),
            "behavior_context": behavior,
            "cart": cart,
            "cart_summary": cart_summary,
            "feature_values": feature_values,
            "preferred_categories": preferred_categories,
            "recent_search_terms": recent_search_terms[-10:],
            "recent_viewed_product_ids": viewed_product_ids[:10],
            "recent_viewed_categories": [name for name, _ in view_category_counter.most_common(5)],
        }
