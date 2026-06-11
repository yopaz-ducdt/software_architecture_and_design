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
    "order": "http://localhost:8003",
    "customer": "http://localhost:8004",
    "staff": "http://localhost:8005",
    "marketing": "http://localhost:8006",
    "inventory": "http://localhost:8007",
    "content": "http://localhost:8008",
    "interaction": "http://localhost:8009",
    "analytics": "http://localhost:8010",
    "behavior": "http://localhost:8013",
}


DEMO_CUSTOMERS = [
    {
        "name": "Minh Anh",
        "email": "minhanh@learnmart.vn",
        "password": "demo123",
        "phone": "0901001001",
        "bio": "Sinh viên năm nhất, hay mua sách kỹ năng và đồ ghi chép.",
        "address": {"street": "12 Nguyễn Văn Cừ", "city": "TP.HCM", "state": "Q5"},
        "persona": "book_focused_student",
        "queries": ["atomic habits", "sách self help giảm giá", "sổ tay b5 campus"],
        "product_skus": ["BOOK-ATOMIC-HABITS", "STA-CAMPUS-B5", "DECOR-MINI-LAMP"],
        "wishlist_indexes": [0, 1],
        "cart": [(0, 1), (1, 3)],
        "orders": [(0, 1), (1, 2)],
    },
    {
        "name": "Quốc Bảo",
        "email": "quocbao@learnmart.vn",
        "password": "demo123",
        "phone": "0901001002",
        "bio": "Học sinh THPT quan tâm máy tính, ba lô và bình nước đi học.",
        "address": {"street": "45 Lê Lợi", "city": "Đà Nẵng", "state": "Hải Châu"},
        "persona": "exam_ready_student",
        "queries": ["casio 580vnx", "balo đi học chống thấm", "bình giữ nhiệt học sinh"],
        "product_skus": ["TECH-CASIO-580VNX", "BAG-MITI-ACTIVE", "BOT-LOCK-500"],
        "wishlist_indexes": [0],
        "cart": [(0, 1), (1, 1)],
        "orders": [(0, 1)],
    },
    {
        "name": "Gia Hân",
        "email": "giahan@learnmart.vn",
        "password": "demo123",
        "phone": "0901001003",
        "bio": "Phụ huynh tìm đồ chơi giáo dục, quà tặng và dụng cụ mỹ thuật.",
        "address": {"street": "88 Trần Phú", "city": "Hà Nội", "state": "Ba Đình"},
        "persona": "parent_gift_buyer",
        "queries": ["lego creative box", "gói quà back to school", "chì màu 24 màu"],
        "product_skus": ["TOY-LEGO-CREATIVE", "GIFT-BTS-01", "ART-FABER-24"],
        "wishlist_indexes": [0, 2],
        "cart": [(0, 1), (1, 1)],
        "orders": [(0, 1), (1, 1), (2, 1)],
    },
    {
        "name": "Thanh Tùng",
        "email": "thanhtung@learnmart.vn",
        "password": "demo123",
        "phone": "0901001004",
        "bio": "Nhân viên văn phòng thích săn voucher và mua combo giá tốt.",
        "address": {"street": "19 Cầu Giấy", "city": "Hà Nội", "state": "Cầu Giấy"},
        "persona": "deal_hunter",
        "queries": ["sale dụng cụ học tập", "voucher learnmart", "coupon bình giữ nhiệt"],
        "product_skus": ["STA-CAMPUS-B5", "BOT-LOCK-500", "SOU-MOJI-CAPY"],
        "wishlist_indexes": [1, 2],
        "cart": [(0, 2), (2, 2)],
        "orders": [(0, 2)],
    },
    {
        "name": "Ngọc Linh",
        "email": "ngoclinh@learnmart.vn",
        "password": "demo123",
        "phone": "0901001005",
        "bio": "Người dùng yêu góc học tập đẹp, thường xem đèn bàn và đồ trang trí.",
        "address": {"street": "27 Pasteur", "city": "TP.HCM", "state": "Q3"},
        "persona": "desk_setup_browser",
        "queries": ["đèn bàn học led", "trang trí bàn học", "móc khóa dễ thương"],
        "product_skus": ["DECOR-MINI-LAMP", "SOU-MOJI-CAPY", "BOT-LOCK-500"],
        "wishlist_indexes": [0],
        "cart": [(0, 1)],
        "orders": [],
    },
    {
        "name": "Hoàng Nam",
        "email": "hoangnam@learnmart.vn",
        "password": "demo123",
        "phone": "0901001006",
        "bio": "Sinh viên mỹ thuật mua màu vẽ, sổ và đồ trang trí bàn học.",
        "address": {"street": "31 Nguyễn Huệ", "city": "Huế", "state": "Phú Hội"},
        "persona": "art_student",
        "queries": ["faber castell 24 màu", "sổ phác thảo", "đèn bàn vẽ"],
        "product_skus": ["ART-FABER-24", "STA-CAMPUS-B5", "DECOR-MINI-LAMP"],
        "wishlist_indexes": [0, 2],
        "cart": [(0, 1), (1, 1)],
        "orders": [(0, 1), (1, 1)],
    },
    {
        "name": "Mai Chi",
        "email": "maichi@learnmart.vn",
        "password": "demo123",
        "phone": "0901001007",
        "bio": "Khách mới chỉ tìm kiếm, xem sản phẩm và chưa mua hàng.",
        "address": {"street": "7 Phan Chu Trinh", "city": "Đà Lạt", "state": "Phường 1"},
        "persona": "new_explorer",
        "queries": ["quà tặng học sinh", "balo miti active", "lego cho bé 6 tuổi"],
        "product_skus": ["GIFT-BTS-01", "BAG-MITI-ACTIVE", "TOY-LEGO-CREATIVE"],
        "wishlist_indexes": [],
        "cart": [],
        "orders": [],
    },
    {
        "name": "Đức Khang",
        "email": "duckhang@learnmart.vn",
        "password": "demo123",
        "phone": "0901001008",
        "bio": "Khách thân thiết mua lặp lại sách, đồ học tập và thiết bị hỗ trợ học.",
        "address": {"street": "101 Võ Văn Tần", "city": "TP.HCM", "state": "Q3"},
        "persona": "loyal_member",
        "queries": ["sách kỹ năng", "casio chính hãng", "combo tựu trường"],
        "product_skus": ["BOOK-ATOMIC-HABITS", "TECH-CASIO-580VNX", "GIFT-BTS-01", "BAG-MITI-ACTIVE"],
        "wishlist_indexes": [1, 3],
        "cart": [(0, 1), (2, 1)],
        "orders": [(0, 1), (1, 1), (2, 1), (3, 1), (0, 2)],
    },
]


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
        f"{BASE['order']}/health",
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


def ensure_customer_account(name, email, password):
    post(
        f"{BASE['auth']}/register/customer",
        {"name": name, "email": email, "password": password},
        f"register customer {email}",
        retries=2,
        delay=1,
    )
    token = post(
        f"{BASE['auth']}/login/customer",
        {"email": email, "password": password},
        f"login customer {email}",
    )
    if not token:
        return 1
    me = get(f"{BASE['auth']}/me?token={token['access_token']}") or {}
    return me.get("user_id", 1)


def ensure_customer():
    return ensure_customer_account("Khách Hàng Demo", "demo@learnmart.vn", "demo123")


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


def get_or_create_profile(customer_id, phone, bio):
    profile = post(
        f"{BASE['customer']}/profile",
        {"customer_id": customer_id, "phone": phone, "bio": bio},
        f"Profile customer {customer_id}",
        retries=2,
        delay=1,
    )
    if not profile:
        profile = get(f"{BASE['customer']}/profile/{customer_id}") or {"id": customer_id}
    return profile


def seed_customer_address(profile_id, address, label):
    post(
        f"{BASE['customer']}/addresses",
        {
            "customer_profile_id": profile_id,
            "street": address["street"],
            "city": address["city"],
            "state": address["state"],
            "is_default": True,
        },
        label,
    )


def category_name_for_product(product):
    category_lookup = {item["slug"]: item["name"] for item in DEFAULT_CATEGORIES}
    return category_lookup.get(product["category_slug"])


def product_lookup_from_catalog(products):
    api_by_sku = {item["sku"]: item for item in products if item.get("sku")}
    by_sku = {}
    for default_product in DEFAULT_PRODUCTS:
        api_product = api_by_sku.get(default_product["sku"])
        if api_product:
            by_sku[default_product["sku"]] = {**default_product, "id": api_product["id"]}
    return by_sku


def behavior_event(customer_id, event_type, *, product=None, query=None, quantity=1, occurred_at=None, metadata=None):
    body = {
        "customer_id": customer_id,
        "event_type": event_type,
        "source": "seed_data",
        "quantity": quantity,
    }
    if occurred_at:
        body["occurred_at"] = occurred_at.isoformat()
    if query:
        body["query"] = query
    if metadata:
        body["metadata"] = metadata
    if product:
        body.update(
            {
                "book_id": product["id"],
                "category_name": category_name_for_product(product),
                "price": product["price"],
            }
        )
    post(f"{BASE['behavior']}/events", body, f"Behavior {event_type} c{customer_id}", retries=2, delay=1)


def seed_customer_journey(customer_id, persona, products_by_sku, start_at):
    selected = []
    for sku in persona["product_skus"]:
        product = products_by_sku.get(sku)
        if product:
            selected.append(product)
    if not selected:
        return

    step = 0
    for query in persona["queries"]:
        behavior_event(
            customer_id,
            "search_performed",
            query=query,
            occurred_at=start_at + timedelta(hours=step),
            metadata={"persona": persona["persona"]},
        )
        step += 1

    for index, product in enumerate(selected):
        behavior_event(
            customer_id,
            "product_viewed",
            product=product,
            occurred_at=start_at + timedelta(hours=step),
            metadata={"rank": index + 1, "persona": persona["persona"]},
        )
        step += 1
        if index == 0:
            behavior_event(
                customer_id,
                "product_clicked_from_listing",
                product=product,
                occurred_at=start_at + timedelta(hours=step),
                metadata={"listing": "search_results"},
            )
            step += 1

    for index in persona["wishlist_indexes"]:
        if index < len(selected):
            product = selected[index]
            post(f"{BASE['customer']}/wishlist/{customer_id}/toggle/{product['id']}", {}, f"Wishlist c{customer_id}")
            behavior_event(
                customer_id,
                "wishlist_added",
                product=product,
                occurred_at=start_at + timedelta(hours=step),
                metadata={"persona": persona["persona"]},
            )
            step += 1

    for index, quantity in persona["cart"]:
        if index < len(selected):
            product = selected[index]
            post(
                f"{BASE['order']}/cart/{customer_id}/add",
                {"book_id": product["id"], "quantity": quantity, "unit_price": product["price"]},
                f"Cart c{customer_id}",
                retries=2,
                delay=1,
            )
            behavior_event(
                customer_id,
                "cart_added",
                product=product,
                quantity=quantity,
                occurred_at=start_at + timedelta(hours=step),
                metadata={"persona": persona["persona"]},
            )
            step += 1

    if persona["cart"]:
        first_cart_product = selected[persona["cart"][0][0]]
        behavior_event(
            customer_id,
            "checkout_started",
            product=first_cart_product,
            quantity=sum(quantity for _, quantity in persona["cart"]),
            occurred_at=start_at + timedelta(hours=step),
            metadata={"payment_method": "COD"},
        )
        step += 1

    for index, quantity in persona["orders"]:
        if index < len(selected):
            product = selected[index]
            behavior_event(
                customer_id,
                "order_completed",
                product=product,
                quantity=quantity,
                occurred_at=start_at + timedelta(hours=step),
                metadata={"coupon_code": "SALE20" if persona["persona"] == "deal_hunter" else None},
            )
            step += 1

    post(f"{BASE['behavior']}/profiles/{customer_id}/refresh", {}, f"Refresh behavior profile c{customer_id}", retries=2, delay=1)


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
    products_by_sku = product_lookup_from_catalog(existing)

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

    log("\n=== Seeding Demo Customers & Behavior Journeys ===")
    journey_start = datetime.now(timezone.utc) - timedelta(days=21)
    demo_customer_ids = []
    for index, persona in enumerate(DEMO_CUSTOMERS, start=1):
        customer = ensure_customer_account(persona["name"], persona["email"], persona["password"])
        demo_customer_ids.append(customer)
        profile = get_or_create_profile(customer, persona["phone"], persona["bio"])
        seed_customer_address(profile.get("id", customer), persona["address"], f"Address c{customer}")
        post(
            f"{BASE['customer']}/newsletter/subscribe",
            {"email": persona["email"]},
            f"Newsletter c{customer}",
            retries=2,
            delay=1,
        )
        seed_customer_journey(customer, persona, products_by_sku, journey_start + timedelta(days=index * 2))

    review_templates = [
        ("Giao nhanh", "Đóng gói chắc chắn, sản phẩm đúng mô tả."),
        ("Phù hợp nhu cầu học tập", "Chất lượng ổn, dùng hằng ngày rất tiện."),
        ("Đáng tiền", "Mức giá hợp lý, sẽ cân nhắc mua thêm."),
        ("Quà tặng đẹp", "Người nhận thích, hình thức bên ngoài chỉn chu."),
    ]
    for index, customer in enumerate(demo_customer_ids[:4]):
        product = list(products_by_sku.values())[index % len(products_by_sku)] if products_by_sku else None
        if not product:
            continue
        title, body = review_templates[index]
        post(
            f"{BASE['product']}/ratings",
            {"product_id": product["id"], "customer_id": customer, "score": 5 - (index % 2)},
            f"rating c{customer}",
            retries=2,
            delay=1,
        )
        post(
            f"{BASE['product']}/reviews",
            {"product_id": product["id"], "customer_id": customer, "title": title, "body": body},
            f"review c{customer}",
            retries=2,
            delay=1,
        )

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
                "book_id": product_ids[0],
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
                "book_id": product_ids[0],
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
