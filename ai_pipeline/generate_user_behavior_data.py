from __future__ import annotations

import csv
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

ACTIONS = [
    "search",
    "view",
    "click",
    "add_to_cart",
    "wishlist",
    "coupon_view",
    "checkout",
    "purchase",
]
CATEGORIES = [
    "Sách",
    "Dụng cụ học tập",
    "Đồ chơi",
    "Gói quà",
    "Ba lô",
    "Bình nước",
    "Đồ điện tử học tập",
    "Mỹ thuật",
    "Đồ trang trí bàn học",
    "Đồ lưu niệm",
]
PERSONAS = ["new_explorer", "category_browser", "deal_hunter", "loyal_member", "high_intent_buyer"]
NEXT_ACTIONS = [
    "recommend_entry_products",
    "push_coupon",
    "bundle_related_products",
    "upsell_membership",
    "reengage_catalog",
]
PRICE_SENSITIVITY = ["low", "medium", "high"]


@dataclass
class PersonaRule:
    persona: str
    action_weights: dict[str, float]
    price_range: tuple[int, int]
    price_sensitivity: str
    next_best_action: str


RULES: dict[str, PersonaRule] = {
    "new_explorer": PersonaRule(
        persona="new_explorer",
        action_weights={"search": 0.28, "view": 0.24, "click": 0.16, "add_to_cart": 0.08, "wishlist": 0.1, "coupon_view": 0.06, "checkout": 0.04, "purchase": 0.04},
        price_range=(35000, 120000),
        price_sensitivity="high",
        next_best_action="recommend_entry_products",
    ),
    "category_browser": PersonaRule(
        persona="category_browser",
        action_weights={"search": 0.18, "view": 0.26, "click": 0.18, "add_to_cart": 0.08, "wishlist": 0.12, "coupon_view": 0.05, "checkout": 0.06, "purchase": 0.07},
        price_range=(50000, 180000),
        price_sensitivity="medium",
        next_best_action="reengage_catalog",
    ),
    "deal_hunter": PersonaRule(
        persona="deal_hunter",
        action_weights={"search": 0.2, "view": 0.18, "click": 0.12, "add_to_cart": 0.1, "wishlist": 0.09, "coupon_view": 0.2, "checkout": 0.07, "purchase": 0.04},
        price_range=(25000, 110000),
        price_sensitivity="high",
        next_best_action="push_coupon",
    ),
    "loyal_member": PersonaRule(
        persona="loyal_member",
        action_weights={"search": 0.08, "view": 0.16, "click": 0.14, "add_to_cart": 0.16, "wishlist": 0.08, "coupon_view": 0.06, "checkout": 0.16, "purchase": 0.16},
        price_range=(120000, 320000),
        price_sensitivity="low",
        next_best_action="upsell_membership",
    ),
    "high_intent_buyer": PersonaRule(
        persona="high_intent_buyer",
        action_weights={"search": 0.1, "view": 0.18, "click": 0.14, "add_to_cart": 0.2, "wishlist": 0.08, "coupon_view": 0.05, "checkout": 0.14, "purchase": 0.11},
        price_range=(90000, 260000),
        price_sensitivity="medium",
        next_best_action="bundle_related_products",
    ),
}

FIELDNAMES = [
    "user_id", "session_id", "step", "timestamp", "product_id",
    "category_name", "action", "price", "quantity", "query",
    "persona_label", "next_best_action", "price_sensitivity",
]


def weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    actions = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(actions, weights=probs, k=1)[0]


def build_dataset(
    out_path: Path,
    user_count: int = 2000,
    seed: int = 42,
    persona_distribution: list[tuple[str, float]] | None = None,
    sequence_length_range: tuple[int, int] = (18, 42),
    dataset_label: str = "base",
) -> dict:
    """
    Build a behavior dataset with configurable persona distribution and sequence length.

    Args:
        out_path: Output CSV path.
        user_count: Number of simulated users.
        seed: Random seed for reproducibility.
        persona_distribution: List of (persona_name, weight) tuples. Weights need not sum to 1.
        sequence_length_range: (min, max) steps per user session chain.
        dataset_label: Human-readable label for logging.
    """
    if persona_distribution is None:
        # Default: balanced distribution
        persona_distribution = [
            ("new_explorer", 0.20),
            ("category_browser", 0.24),
            ("deal_hunter", 0.20),
            ("loyal_member", 0.16),
            ("high_intent_buyer", 0.20),
        ]

    rng = random.Random(seed)
    start = datetime(2026, 1, 1, 8, 0, 0)
    rows: list[dict] = []
    persona_counts: defaultdict[str, int] = defaultdict(int)

    persona_labels = [name for name, _ in persona_distribution]
    persona_weights = [weight for _, weight in persona_distribution]

    for user_id in range(1, user_count + 1):
        persona = rng.choices(persona_labels, weights=persona_weights, k=1)[0]
        persona_counts[persona] += 1
        rule = RULES[persona]
        base_category = rng.choice(CATEGORIES)
        sequence_length = rng.randint(*sequence_length_range)
        event_time = start + timedelta(hours=rng.randint(0, 24 * 45))
        session_index = 1
        purchase_count = 0

        for step in range(sequence_length):
            action = weighted_choice(rng, rule.action_weights)
            if action in {"checkout", "purchase"} and step < 4:
                action = rng.choice(["search", "view", "click"])
            if action == "purchase":
                purchase_count += 1
            if action == "purchase" and purchase_count > 3:
                action = rng.choice(["view", "add_to_cart", "checkout"])

            category_name = base_category if rng.random() < 0.65 else rng.choice(CATEGORIES)
            price = rng.randint(*rule.price_range)
            quantity = 1 if action != "purchase" else rng.randint(1, 2)

            if action == "coupon_view":
                query = rng.choice(["voucher", "sale", "coupon học tập", "khuyến mãi"])
            elif action == "search":
                query = rng.choice([
                    f"{category_name.lower()} giá tốt",
                    f"{category_name.lower()} cho học sinh",
                    f"mua {category_name.lower()} online",
                    f"{category_name.lower()} dưới {price // 1000}k",
                ])
            else:
                query = ""

            rows.append({
                "user_id": user_id,
                "session_id": f"S{user_id:04d}-{session_index:02d}",
                "step": step + 1,
                "timestamp": event_time.isoformat(),
                "product_id": rng.randint(1000, 1300),
                "category_name": category_name,
                "action": action,
                "price": price,
                "quantity": quantity,
                "query": query,
                "persona_label": persona,
                "next_best_action": rule.next_best_action,
                "price_sensitivity": rule.price_sensitivity,
            })

            event_time += timedelta(minutes=rng.randint(2, 45))
            if rng.random() < 0.12:
                session_index += 1
                event_time += timedelta(hours=rng.randint(4, 36))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    stats = {
        "dataset": dataset_label,
        "path": str(out_path),
        "total_users": user_count,
        "total_rows": len(rows),
        "avg_sequence_length": round(len(rows) / user_count, 1),
        "sequence_length_range": sequence_length_range,
        "persona_counts": dict(sorted(persona_counts.items())),
    }
    return stats


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent / "data"

    # ──────────────────────────────────────────────
    # DATASET 1 — Baseline (balanced distribution)
    # Mô phỏng: ngày thường, traffic đa dạng
    # ──────────────────────────────────────────────
    stats1 = build_dataset(
        out_path=base_dir / "dataset1_baseline.csv",
        user_count=2000,
        seed=42,
        persona_distribution=[
            ("new_explorer",     0.20),
            ("category_browser", 0.24),
            ("deal_hunter",      0.20),
            ("loyal_member",     0.16),
            ("high_intent_buyer",0.20),
        ],
        sequence_length_range=(18, 42),
        dataset_label="Dataset 1 — Baseline (Balanced)",
    )

    # ──────────────────────────────────────────────
    # DATASET 2 — Flash Sale Season
    # Mô phỏng: mùa sale/khuyến mãi lớn
    # deal_hunter tăng mạnh, loyal_member tăng nhẹ
    # high_intent_buyer tăng (mua nhiều hơn khi có deal)
    # Sequence dài hơn vì user browse nhiều hơn
    # ──────────────────────────────────────────────
    stats2 = build_dataset(
        out_path=base_dir / "dataset2_flash_sale.csv",
        user_count=2000,
        seed=123,
        persona_distribution=[
            ("new_explorer",     0.10),
            ("category_browser", 0.15),
            ("deal_hunter",      0.38),
            ("loyal_member",     0.22),
            ("high_intent_buyer",0.15),
        ],
        sequence_length_range=(22, 55),
        dataset_label="Dataset 2 — Flash Sale Season",
    )

    # ──────────────────────────────────────────────
    # DATASET 3 — Cold Start / New User Heavy
    # Mô phỏng: đầu năm học, nhiều user mới
    # new_explorer chiếm đa số
    # Sequence ngắn hơn (user chưa quen platform)
    # Ít purchase, nhiều search/view
    # ──────────────────────────────────────────────
    stats3 = build_dataset(
        out_path=base_dir / "dataset3_cold_start.csv",
        user_count=2000,
        seed=777,
        persona_distribution=[
            ("new_explorer",     0.55),
            ("category_browser", 0.25),
            ("deal_hunter",      0.08),
            ("loyal_member",     0.04),
            ("high_intent_buyer",0.08),
        ],
        sequence_length_range=(5, 18),
        dataset_label="Dataset 3 — Cold Start / New User Heavy",
    )

    # ──────────────────────────────────────────────
    # Print summary
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DATASET GENERATION COMPLETE")
    print("=" * 60)
    for stats in [stats1, stats2, stats3]:
        print(f"\n📦 {stats['dataset']}")
        print(f"   Path            : {stats['path']}")
        print(f"   Users           : {stats['total_users']}")
        print(f"   Total rows      : {stats['total_rows']}")
        print(f"   Avg seq length  : {stats['avg_sequence_length']} steps")
        print(f"   Seq range       : {stats['sequence_length_range']}")
        print(f"   Persona counts  :")
        for persona, count in stats['persona_counts'].items():
            pct = round(count / stats['total_users'] * 100, 1)
            print(f"      {persona:<22} {count:>4} users ({pct}%)")
    print("\n" + "=" * 60)