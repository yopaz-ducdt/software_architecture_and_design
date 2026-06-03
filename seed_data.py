"""Seed demo data for LearnMart marketplace."""
from __future__ import annotations

import io
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

from seed_catalog import DEFAULT_BRANDS, DEFAULT_CATEGORIES, DEFAULT_PRODUCT_TYPES, DEFAULT_PRODUCTS

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


BASE = {
    "auth": "http://localhost:8001",
    "product": "http://localhost:8002",
    "customer": "http://localhost:8004",
    "staff": "http://localhost:8005",
    "marketing": "http://localhost:8006",
    "inventory": "http://localhost:8007",
    "content": "http://localhost:8008",
    "interaction": "http://localhost:8009",
    "analytics": "http://localhost:8010",
    "behavior": "http://localhost:8013",
}


def log(message):
    print(message, flush=True)


def log_step(message):
    log(f"[STEP] {message}")


def log_ok(message):
    log(f"[OK] {message}")


def log_warn(message):
    log(f"[WARN] {message}")


def post(url, body, label="", retries=10, delay=2):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=body, timeout=10)
            if response.status_code in (200, 201):
                if label:
                    log_ok(f"{label}")
                return response.json() if response.content else None
            if response.status_code in (400, 409):
                try:
                    data = response.json()
                except Exception:
                    data = {"detail": response.text}
                log_warn(f"[{response.status_code}] {label}: {data}")
                return None
            last_error = RuntimeError(f"{response.status_code} {response.text[:300]}")
        except Exception as exc:
            last_error = exc
            if label:
                log_warn(f"{label} failed on attempt {attempt}/{retries}: {exc}")
        time.sleep(delay)
    log_warn(f"ERR {label}: {last_error}")
    return None


def get(url, retries=10, delay=2):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=10)
            if response.ok:
                return response.json()
            last_error = RuntimeError(f"{response.status_code} {response.text[:300]}")
        except Exception as exc:
            last_error = exc
            log_warn(f"GET failed on attempt {attempt}/{retries}: {url} -> {exc}")
        time.sleep(delay)
    log_warn(f"ERR GET {url}: {last_error}")
    return None


def wait_services():
    health_urls = [
        f"{BASE['auth']}/health",
        f"{BASE['product']}/health",
        f"{BASE['customer']}/health",
        f"{BASE['staff']}/health",
        f"{BASE['marketing']}/health",
        f"{BASE['inventory']}/health",
        f"{BASE['content']}/health",
        f"{BASE['interaction']}/health",
        f"{BASE['analytics']}/health",
        f"{BASE['behavior']}/health",
    ]
    for url in health_urls:
        log_step(f"Waiting for {url}")
        ok = False
        for attempt in range(1, 41):
            try:
                response = requests.get(url, timeout=5)
                if response.ok:
                    ok = True
                    log_ok(f"Health ready: {url}")
                    break
            except Exception:
                pass
            if attempt in (1, 5, 10, 20, 30, 40):
                log_warn(f"Still waiting ({attempt}/40): {url}")
            time.sleep(2)
        if not ok:
            log_warn(f"Health not ready: {url}")


def ensure_customer():
    post(
        f"{BASE['auth']}/register/customer",
        {"name": "Khách Hàng Demo", "email": "demo@learnmart.vn", "password": "demo123"},
        "register customer",
        retries=2,
        delay=1,
    )
    token = post(
        f"{BASE['auth']}/login/customer",
        {"email": "demo@learnmart.vn", "password": "demo123"},
        "login customer",
    )
    if not token:
        return 1
    me = get(f"{BASE['auth']}/me?token={token['access_token']}") or {}
    return me.get("user_id", 1)


def ensure_staff():
    post(
        f"{BASE['auth']}/register/staff",
        {"name": "Admin Staff", "username": "admin", "password": "admin123", "role": "ADMIN"},
        "register staff",
        retries=2,
        delay=1,
    )
    token = post(
        f"{BASE['auth']}/login/staff",
        {"username": "admin", "password": "admin123"},
        "login staff",
    )
    if not token:
        return 1
    me = get(f"{BASE['auth']}/me?token={token['access_token']}") or {}
    return me.get("user_id", 1)


def get_slug_map(items):
    return {item["slug"]: item["id"] for item in items if "slug" in item}


def build_product_payloads(category_map, type_map, brand_map):
    return [
        {
            "name": product["name"],
            "sku": product["sku"],
            "price": product["price"],
            "stock_quantity": product["stock_quantity"],
            "category_id": category_map.get(product["category_slug"]),
            "product_type_id": type_map.get(product["product_type_slug"]),
            "brand_id": brand_map.get(product["brand_slug"]),
            "description": product["description"],
            "attributes": product["attributes"],
        }
        for product in DEFAULT_PRODUCTS
    ]


def main():
    wait_services()
    log("\n=== Seeding Accounts ===")
    customer_id = ensure_customer()
    staff_id = ensure_staff()
    log_ok(f"Accounts ready: customer_id={customer_id}, staff_id={staff_id}")

    log("\n=== Seeding Catalog ===")
    for index, category in enumerate(DEFAULT_CATEGORIES, start=1):
        log_step(f"Category {index}/{len(DEFAULT_CATEGORIES)}: {category['name']}")
        post(f"{BASE['product']}/categories", category, category["name"], retries=2, delay=1)

    for index, product_type in enumerate(DEFAULT_PRODUCT_TYPES, start=1):
        log_step(f"Product type {index}/{len(DEFAULT_PRODUCT_TYPES)}: {product_type['name']}")
        post(f"{BASE['product']}/product-types", product_type, product_type["name"], retries=2, delay=1)

    for index, brand in enumerate(DEFAULT_BRANDS, start=1):
        log_step(f"Brand {index}/{len(DEFAULT_BRANDS)}: {brand['name']}")
        post(f"{BASE['product']}/brands", brand, brand["name"], retries=2, delay=1)

    categories = get(f"{BASE['product']}/categories") or []
    product_types = get(f"{BASE['product']}/product-types") or []
    brands = get(f"{BASE['product']}/brands") or []
    category_map = get_slug_map(categories)
    type_map = get_slug_map(product_types)
    brand_map = get_slug_map(brands)

    catalog = build_product_payloads(category_map, type_map, brand_map)
    product_ids = []
    for index, item in enumerate(catalog, start=1):
        log_step(f"Product {index}/{len(catalog)}: {item['name']}")
        created = post(f"{BASE['product']}/products", item, item["name"], retries=2, delay=1)
        if created:
            product_ids.append(created["id"])

    existing = get(f"{BASE['product']}/products?limit=50") or []
    if not product_ids:
        product_ids = [item["id"] for item in existing[:10]]

    log("\n=== Seeding Product Ratings & Reviews ===")
    if product_ids:
        post(
            f"{BASE['product']}/ratings",
            {"product_id": product_ids[0], "customer_id": customer_id, "score": 5},
            "rating",
        )
        post(
            f"{BASE['product']}/reviews",
            {
                "product_id": product_ids[0],
                "customer_id": customer_id,
                "title": "Rất tốt",
                "body": "Sản phẩm hữu ích, đúng với mô tả.",
            },
            "review",
        )

    log("\n=== Seeding Marketing ===")
    post(
        f"{BASE['marketing']}/coupons",
        {"code": "SALE20", "discount_percent": 20, "min_order_value": 100000, "max_uses": 100},
        "SALE20",
    )
    post(
        f"{BASE['marketing']}/promotions",
        {
            "name": "Mùa Tựu Trường",
            "description": "Giảm giá cho sách, dụng cụ học tập và phụ kiện đi học.",
            "discount_percent": 10,
        },
        "Promo",
    )
    now = datetime.now(timezone.utc)
    if product_ids:
        post(
            f"{BASE['marketing']}/flash-sales",
            {
                "name": "Flash Sale tựu trường",
                "discount_percent": 25,
                "max_quantity": 50,
                "start_at": now.isoformat(),
                "end_at": (now + timedelta(days=3)).isoformat(),
                "product_id": product_ids[0],
            },
            "FlashSale",
        )
    post(f"{BASE['marketing']}/tiers/seed", {}, "Seed Tiers")

    log("\n=== Seeding Customer Data ===")
    profile = post(
        f"{BASE['customer']}/profile",
        {"customer_id": customer_id, "phone": "0912345678", "bio": "Yêu mua sắm đồ học tập và quà tặng nhỏ."},
        "Profile",
        retries=2,
        delay=1,
    )
    if not profile:
        profile = get(f"{BASE['customer']}/profile/{customer_id}") or {"id": 1}
    profile_id = profile.get("id", 1)
    post(
        f"{BASE['customer']}/addresses",
        {"customer_profile_id": profile_id, "street": "123 Đường A", "city": "TP.HCM", "state": "Q1"},
        "Address",
    )
    if product_ids:
        post(f"{BASE['customer']}/wishlist/{customer_id}/toggle/{product_ids[0]}", {}, "Wishlist")

    log("\n=== Seeding Staff / Inventory / Content ===")
    department = post(
        f"{BASE['staff']}/departments",
        {"name": "IT", "description": "Tech Team"},
        "Department",
        retries=2,
        delay=1,
    )
    if not department:
        departments = get(f"{BASE['staff']}/departments") or []
        department = departments[0] if departments else {"id": 1}
    department_id = department.get("id", 1)
    post(
        f"{BASE['staff']}/members",
        {"staff_id": staff_id, "department_id": department_id, "phone": "0900000000", "salary": 15000000},
        "Staff Member",
    )
    post(
        f"{BASE['inventory']}/warehouses",
        {"name": "Kho Miền Nam", "location": "TPHCM", "capacity": 5000},
        "Warehouse",
    )
    post(
        f"{BASE['inventory']}/suppliers",
        {"name": "Campus Vietnam", "contact_name": "CSKH", "email": "hello@campus.vn"},
        "Supplier",
    )
    post(
        f"{BASE['content']}/banners",
        {
            "title": "Back To School",
            "subtitle": "Ưu đãi mùa tựu trường",
            "image_url": "https://example.com/banner.jpg",
            "link_url": "/",
            "order": 1,
        },
        "Banner",
    )
    post(
        f"{BASE['content']}/blog",
        {
            "title": "Top sản phẩm mùa tựu trường",
            "slug": "top-san-pham-mua-tuu-truong",
            "body": "Gợi ý sách, bút, ba lô và quà tặng cho mùa tựu trường.",
            "author_name": "Admin Staff",
        },
        "Blog",
    )
    post(
        f"{BASE['interaction']}/gift-cards",
        {
            "amount": 100000,
            "buyer_customer_id": customer_id,
            "recipient_email": "friend@example.com",
            "message": "Happy learning!",
        },
        "GiftCard",
    )

    log("\n=== Seeding Analytics ===")
    post(
        f"{BASE['analytics']}/search-history",
        {"customer_id": customer_id, "query": "lego creative", "results_count": 1},
        "Search",
    )
    if product_ids:
        post(
            f"{BASE['analytics']}/recently-viewed",
            {"customer_id": customer_id, "product_id": product_ids[0]},
            "Recent view",
        )

    log("\n=== Seeding Behavior ===")
    post(
        f"{BASE['behavior']}/events",
        {"customer_id": customer_id, "event_type": "search_performed", "query": "casio học tập", "source": "seed"},
        "Behavior search",
    )
    if product_ids:
        first_product = DEFAULT_PRODUCTS[0]
        category_lookup = {item["slug"]: item["name"] for item in DEFAULT_CATEGORIES}
        category_name = category_lookup[first_product["category_slug"]]
        post(
            f"{BASE['behavior']}/events",
            {
                "customer_id": customer_id,
                "event_type": "product_viewed",
                "product_id": product_ids[0],
                "category_name": category_name,
                "price": first_product["price"],
                "source": "seed",
            },
            "Behavior view",
        )
        post(
            f"{BASE['behavior']}/events",
            {
                "customer_id": customer_id,
                "event_type": "cart_added",
                "product_id": product_ids[0],
                "category_name": category_name,
                "price": first_product["price"],
                "quantity": 1,
                "source": "seed",
            },
            "Behavior cart",
        )
        post(f"{BASE['behavior']}/profiles/{customer_id}/refresh", {}, "Refresh behavior profile")

    log("\nSeed completed.")


if __name__ == "__main__":
    main()
