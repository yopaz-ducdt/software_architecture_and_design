"""Bulk seed products into the LearnMart product service.

Usage:
  python seed_products_bulk.py [count]

Example:
  python seed_products_bulk.py 50
"""
from __future__ import annotations

import json
import random
import sys
import time
from typing import Any

import requests

BASE = {
    "product": "http://localhost:8002",
}

HEADERS = {
    "Content-Type": "application/json",
}

CATEGORY_DEFINITIONS = [
    {"name": "Sách", "slug": "books", "description": "Sách và ấn phẩm học tập, phát triển bản thân."},
    {"name": "Dụng cụ học tập", "slug": "stationery", "description": "Bút, sổ, giấy note và dụng cụ học tập hằng ngày."},
    {"name": "Đồ chơi", "slug": "toys", "description": "Đồ chơi giáo dục và sáng tạo cho trẻ em."},
    {"name": "Gói quà", "slug": "gift-packs", "description": "Combo quà tặng theo chủ đề học tập và sinh nhật."},
    {"name": "Ba lô", "slug": "backpacks", "description": "Ba lô đi học và di chuyển ngắn ngày."},
    {"name": "Bình nước", "slug": "water-bottles", "description": "Bình nước giữ nhiệt và thể thao cho ngày học dài."},
    {"name": "Đồ điện tử học tập", "slug": "study-tech", "description": "Thiết bị hỗ trợ học tập như máy tính và đèn học."},
    {"name": "Mỹ thuật", "slug": "art-supplies", "description": "Dụng cụ vẽ, tô màu và thủ công sáng tạo."},
    {"name": "Đồ trang trí bàn học", "slug": "desk-decor", "description": "Phụ kiện giúp góc học tập gọn gàng và truyền cảm hứng."},
    {"name": "Đồ lưu niệm", "slug": "souvenirs", "description": "Quà tặng và vật phẩm dễ thương để sưu tầm."},
]

PRODUCT_TYPE_DEFINITIONS = [
    {"name": "Book", "slug": "book", "description": "Printed books and learning publications."},
    {"name": "Stationery", "slug": "stationery", "description": "School and office stationery."},
    {"name": "Toy", "slug": "toy", "description": "Educational and creative toys."},
    {"name": "Gift Pack", "slug": "gift-pack", "description": "Curated gift bundles."},
    {"name": "Backpack", "slug": "backpack", "description": "Backpacks and carrying bags."},
    {"name": "Bottle", "slug": "bottle", "description": "Reusable bottles and tumblers."},
    {"name": "Study Tech", "slug": "study-tech", "description": "Study-support electronics and devices."},
    {"name": "Art Supply", "slug": "art-supply", "description": "Art and craft supplies."},
    {"name": "Desk Decor", "slug": "desk-decor", "description": "Desk accessories and decor."},
    {"name": "Souvenir", "slug": "souvenir", "description": "Souvenirs and collectible accessories."},
]

BRAND_DEFINITIONS = [
    {"name": "NXB Trẻ", "slug": "nxb-tre"},
    {"name": "Campus", "slug": "campus"},
    {"name": "LEGO", "slug": "lego"},
    {"name": "GiftHub", "slug": "gifthub"},
    {"name": "Miti", "slug": "miti"},
    {"name": "LocknLock", "slug": "locknlock"},
    {"name": "Casio", "slug": "casio"},
    {"name": "Faber-Castell", "slug": "faber-castell"},
    {"name": "Minihome", "slug": "minihome"},
    {"name": "Moji", "slug": "moji"},
]

CATEGORY_TO_TYPE = {
    "books": "book",
    "stationery": "stationery",
    "toys": "toy",
    "gift-packs": "gift-pack",
    "backpacks": "backpack",
    "water-bottles": "bottle",
    "study-tech": "study-tech",
    "art-supplies": "art-supply",
    "desk-decor": "desk-decor",
    "souvenirs": "souvenir",
}

PRICE_RANGES = {
    "books": (79000, 249000),
    "stationery": (19000, 99000),
    "toys": (99000, 549000),
    "gift-packs": (99000, 259000),
    "backpacks": (249000, 599000),
    "water-bottles": (99000, 299000),
    "study-tech": (199000, 1299000),
    "art-supplies": (59000, 299000),
    "desk-decor": (79000, 399000),
    "souvenirs": (49000, 159000),
}

TEMPLATES = {
    "books": [
        "Sách kỹ năng {word}",
        "Combo sách {word}",
        "Sách học {word}",
        "Tuyển tập {word}",
    ],
    "stationery": [
        "Sổ tay {word}",
        "Bút gel {word}",
        "Set văn phòng {word}",
        "Giấy note {word}",
    ],
    "toys": [
        "Đồ chơi {word}",
        "Bộ xếp hình {word}",
        "Robot {word}",
        "Đồ chơi giáo dục {word}",
    ],
    "gift-packs": [
        "Gói quà {word}",
        "Set quà tặng {word}",
        "Combo quà {word}",
        "Hộp quà {word}",
    ],
    "backpacks": [
        "Ba lô {word}",
        "Túi xách {word}",
        "Balo học {word}",
        "Balo du lịch {word}",
    ],
    "water-bottles": [
        "Bình nước {word}",
        "Bình giữ nhiệt {word}",
        "Bình thể thao {word}",
        "Bình du lịch {word}",
    ],
    "study-tech": [
        "Đèn học {word}",
        "Tai nghe {word}",
        "Chuột không dây {word}",
        "Bàn phím mini {word}",
    ],
    "art-supplies": [
        "Bút màu {word}",
        "Sơn acrylic {word}",
        "Bộ vẽ {word}",
        "Dụng cụ mỹ thuật {word}",
    ],
    "desk-decor": [
        "Đèn bàn {word}",
        "Kệ sách mini {word}",
        "Thảm chuột {word}",
        "Trang trí bàn {word}",
    ],
    "souvenirs": [
        "Móc khóa {word}",
        "Sticker {word}",
        "Túi vải {word}",
        "Thẻ treo {word}",
    ],
}

FLOW_WORDS = [
    "Galaxy", "Classic", "Smart", "Cool", "Retro", "Mini", "Pro", "Light", "Happy", "Lucky", "Magic", "Fresh", "Zen", "Eco", "Urban", "Color", "Dream", "Spark", "Fun", "Active",
]

ATTRIBUTE_TEMPLATES = {
    "books": lambda idx: {"language": "vi", "pages": 100 + idx * 2},
    "stationery": lambda idx: {"color": random.choice(["xanh", "hồng", "đen", "vàng"]), "size": random.choice(["A4", "A5", "B5"] )},
    "toys": lambda idx: {"age_group": random.choice(["3+", "6+", "8+"]), "type": random.choice(["lego", "robot", "puzzle"])},
    "gift-packs": lambda idx: {"items": random.choice([3, 4, 5, 6]), "occasion": random.choice(["sinh nhật", "tựu trường", "tốt nghiệp"])},
    "backpacks": lambda idx: {"capacity": random.choice(["15L", "18L", "20L", "25L"]), "material": random.choice(["vải", "da tổng hợp"] )},
    "water-bottles": lambda idx: {"volume": random.choice(["400ml", "500ml", "650ml"]), "material": random.choice(["inox", "nhựa"] )},
    "study-tech": lambda idx: {"feature": random.choice(["LED", "Bluetooth", "USB", "Pin sạc"] ), "brand": random.choice(["Smart", "Neo", "ProTech"] )},
    "art-supplies": lambda idx: {"colors": random.choice([12, 18, 24, 36]), "type": random.choice(["chì", "màu", "sơn"] )},
    "desk-decor": lambda idx: {"style": random.choice(["modern", "vintage", "minimal"]), "material": random.choice(["gỗ", "nhựa", "kim loại"] )},
    "souvenirs": lambda idx: {"theme": random.choice(["động vật", "hoạt hình", "tự nhiên"]), "material": random.choice(["vải", "kim loại", "nhựa"] )},
}


def log(message: str) -> None:
    print(message)


def request_json(method: str, path: str, payload: Any | None = None, retries: int = 3, delay: float = 1.0) -> Any:
    url = BASE["product"] + path
    for attempt in range(1, retries + 1):
        try:
            response = requests.request(method, url, headers=HEADERS, json=payload, timeout=10)
            if response.status_code in (200, 201):
                return response.json()
            if response.status_code == 204:
                return None
            log(f"[{response.status_code}] {method} {url} => {response.text}")
        except requests.RequestException as exc:
            log(f"Request failed ({attempt}/{retries}): {exc}")
        if attempt < retries:
            time.sleep(delay)
    raise RuntimeError(f"Failed request {method} {url}")


def get_json(path: str) -> Any:
    return request_json("GET", path)


def post_json(path: str, payload: Any) -> Any:
    return request_json("POST", path, payload)


def ensure_entities(path: str, items: list[dict[str, Any]], item_name: str) -> dict[str, int]:
    existing = get_json(path) or []
    slug_to_id = {item["slug"]: item["id"] for item in existing if item.get("slug") and item.get("id")}
    for item in items:
        if item["slug"] in slug_to_id:
            continue
        log(f"Creating {item_name}: {item['name']}")
        created = post_json(path, item)
        slug_to_id[item["slug"]] = created["id"]
    return slug_to_id


def build_product_payloads(count: int, category_map: dict[str, int], type_map: dict[str, int], brand_map: dict[str, int]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    category_slugs = list(CATEGORY_TO_TYPE.keys())
    used_skus = set()
    for idx in range(1, count + 1):
        category_slug = random.choice(category_slugs)
        template = random.choice(TEMPLATES[category_slug])
        word = random.choice(FLOW_WORDS)
        name = template.format(word=word)
        sku = f"{category_slug[:3].upper()}-{word.upper()}-{idx:03d}".replace(" ", "-")
        sku = sku[:40]
        if sku in used_skus:
            sku = f"{sku}-{idx}"
        used_skus.add(sku)

        min_price, max_price = PRICE_RANGES[category_slug]
        price = random.randrange(min_price // 1000, max_price // 1000) * 1000
        brand_slug = random.choice(list(brand_map.keys()))
        product_type_slug = CATEGORY_TO_TYPE[category_slug]
        attributes = ATTRIBUTE_TEMPLATES[category_slug](idx)
        image_seed = sku.lower().replace(" ", "-")
        payloads.append({
            "name": name,
            "sku": sku,
            "price": price,
            "stock_quantity": random.randint(20, 250),
            "category_id": category_map[category_slug],
            "product_type_id": type_map[product_type_slug],
            "brand_id": brand_map[brand_slug],
            "description": f"{name} chất lượng cao, phù hợp cho nhu cầu học tập và giải trí.",
            "image_url": f"https://picsum.photos/seed/{image_seed}/400/600",
            "attributes": attributes,
        })
    return payloads


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    log(f"Bulk seeding {count} products into product service...")

    category_map = ensure_entities("/categories", CATEGORY_DEFINITIONS, "category")
    type_map = ensure_entities("/product-types", PRODUCT_TYPE_DEFINITIONS, "product type")
    brand_map = ensure_entities("/brands", BRAND_DEFINITIONS, "brand")

    payloads = build_product_payloads(count, category_map, type_map, brand_map)
    created_ids = []
    for index, payload in enumerate(payloads, start=1):
        log(f"Creating product {index}/{count}: {payload['name']} ({payload['sku']})")
        created = post_json("/products", payload)
        created_ids.append(created["id"])

    log("Bulk seed completed.")
    print(json.dumps({"created_product_ids": created_ids, "count": len(created_ids)}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
