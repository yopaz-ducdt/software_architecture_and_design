from __future__ import annotations

import io
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


BASE = {
    "auth": "http://localhost:8001",
    "product": "http://localhost:8002",
    "customer": "http://localhost:8004",
    "marketing": "http://localhost:8006",
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


def post(url, body, retries=12, delay=2):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, json=body, timeout=8)
            if response.status_code in (200, 201):
                return response.json() if response.content else None
            if response.status_code in (400, 409):
                try:
                    return response.json()
                except Exception:
                    return {"detail": response.text}
            last_error = RuntimeError(f"{response.status_code} {response.text[:300]}")
        except Exception as exc:
            last_error = exc
            log_warn(f"POST failed on attempt {attempt}/{retries}: {url} -> {exc}")
        time.sleep(delay)
    raise last_error


def get(url, retries=12, delay=2):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            log_warn(f"GET failed on attempt {attempt}/{retries}: {url} -> {exc}")
            time.sleep(delay)
    raise last_error


def wait_services():
    for url in [
        f"{BASE['auth']}/health",
        f"{BASE['product']}/health",
        f"{BASE['customer']}/health",
        f"{BASE['marketing']}/health",
        f"{BASE['analytics']}/health",
        f"{BASE['behavior']}/health",
    ]:
        log_step(f"Waiting for {url}")
        for attempt in range(1, 41):
            try:
                response = requests.get(url, timeout=5)
                if response.ok:
                    log_ok(f"Health ready: {url}")
                    break
            except Exception:
                pass
            if attempt in (1, 5, 10, 20, 30, 40):
                log_warn(f"Still waiting ({attempt}/40): {url}")
            time.sleep(2)


def ensure_customer():
    try:
        log_step("Registering demo customer if needed")
        post(
            f"{BASE['auth']}/register/customer",
            {"name": "Khách Hàng Demo", "email": "demo@learnmart.vn", "password": "demo123"},
            retries=2,
            delay=1,
        )
    except Exception:
        pass
    log_step("Logging in demo customer")
    token = post(f"{BASE['auth']}/login/customer", {"email": "demo@learnmart.vn", "password": "demo123"})
    me = get(f"{BASE['auth']}/me?token={token['access_token']}")
    log_ok(f"Customer ready: id={me['user_id']}")
    return me["user_id"]


def seed_behavior(customer_id, product_ids):
    if product_ids:
        log_step("Seeding wishlist and recently viewed")
        post(f"{BASE['customer']}/wishlist/{customer_id}/toggle/{product_ids[0]}", {})
        post(f"{BASE['analytics']}/recently-viewed", {"customer_id": customer_id, "product_id": product_ids[0]})
        if len(product_ids) > 1:
            post(f"{BASE['analytics']}/recently-viewed", {"customer_id": customer_id, "product_id": product_ids[1]})
    now = datetime.now(timezone.utc)
    log_step("Seeding membership tiers and coupon")
    post(f"{BASE['marketing']}/tiers/seed", {})
    try:
        post(
            f"{BASE['marketing']}/coupons",
            {"code": "AI10", "discount_percent": 10, "min_order_value": 50000},
            retries=2,
            delay=1,
        )
    except Exception:
        pass
    if product_ids:
        log_step("Seeding flash sale and behavior events")
        post(
            f"{BASE['marketing']}/flash-sales",
            {
                "name": "Flash Sale tựu trường",
                "discount_percent": 15,
                "max_quantity": 30,
                "start_at": now.isoformat(),
                "end_at": (now + timedelta(days=2)).isoformat(),
                "product_id": product_ids[0],
            },
        )
        post(
            f"{BASE['behavior']}/events",
            {
                "customer_id": customer_id,
                "event_type": "product_viewed",
                "product_id": product_ids[0],
                "source": "seed_ai_demo",
            },
        )
        post(
            f"{BASE['behavior']}/events",
            {
                "customer_id": customer_id,
                "event_type": "wishlist_added",
                "product_id": product_ids[0],
                "source": "seed_ai_demo",
            },
        )
        post(f"{BASE['behavior']}/profiles/{customer_id}/refresh", {})
        log_ok("Behavior profile refreshed")


def seed_products():
    log_step("Loading seeded products")
    existing = get(f"{BASE['product']}/products?limit=20") or []
    product_ids = [item["id"] for item in existing[:3]]
    log_ok(f"Loaded {len(product_ids)} product ids for AI demo")
    return product_ids


if __name__ == "__main__":
    log("=== Seed AI Demo ===")
    wait_services()
    customer_id = ensure_customer()
    product_ids = seed_products()
    seed_behavior(customer_id, product_ids)
    log("Seed AI demo xong. Dùng tài khoản demo@learnmart.vn / demo123 để test AI chatbot.")
