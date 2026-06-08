from __future__ import annotations

import csv
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────
ACTIONS = [
    "search", "view", "click", "add_to_cart",
    "wishlist", "coupon_view", "checkout", "purchase",
]

CATEGORIES = [
    "Sách", "Dụng cụ học tập", "Đồ chơi", "Gói quà", "Ba lô",
    "Bình nước", "Đồ điện tử học tập", "Mỹ thuật",
    "Đồ trang trí bàn học", "Đồ lưu niệm",
]

PERSONAS = [
    "new_explorer", "category_browser", "deal_hunter",
    "loyal_member", "high_intent_buyer",
]

NEXT_ACTIONS = [
    "recommend_entry_products", "push_coupon",
    "bundle_related_products", "upsell_membership", "reengage_catalog",
]

FIELDNAMES = [
    "user_id", "session_id", "step", "timestamp", "product_id",
    "category_name", "action", "price", "quantity", "query",
    "persona_label", "next_best_action", "price_sensitivity",
]


# ─────────────────────────────────────────────────────────────
# Persona Journey Phases
# ─────────────────────────────────────────────────────────────
# Mỗi persona được định nghĩa bởi 3 PHASE tuần tự:
#   EARLY  → MIDDLE → LATE
# Mỗi phase có action_weights riêng phản ánh hành vi đặc trưng
# tại từng giai đoạn của hành trình mua hàng.
#
# Ý nghĩa thiết kế:
#   - LSTM/biLSTM học được sự chuyển đổi giữa các phase
#   - MLP chỉ thấy tổng hợp toàn bộ sequence → mất tín hiệu phase
#   - Tần suất tổng thể vẫn giống nhau giữa các model
#     (MLP không bị thiệt thòi về feature, chỉ thiếu thông tin thứ tự)

@dataclass
class PersonaJourney:
    persona:           str
    price_range:       tuple[int, int]
    price_sensitivity: str
    next_best_action:  str
    # Mỗi phase: dict action → weight, cộng thêm tỉ lệ độ dài phase
    early_weights:  dict[str, float] = field(default_factory=dict)   # ~30% đầu
    middle_weights: dict[str, float] = field(default_factory=dict)   # ~40% giữa
    late_weights:   dict[str, float] = field(default_factory=dict)   # ~30% cuối


JOURNEYS: dict[str, PersonaJourney] = {

    # ── new_explorer ──────────────────────────────────────────
    # Hành trình: Tìm kiếm nhiều → Browse → Thỉnh thoảng wishlist, hiếm mua
    # EARLY : search nặng (khám phá)
    # MIDDLE: view + click (đang cân nhắc)
    # LATE  : wishlist hoặc rời đi (chưa quyết định)
    "new_explorer": PersonaJourney(
        persona="new_explorer",
        price_range=(35_000, 120_000),
        price_sensitivity="high",
        next_best_action="recommend_entry_products",
        early_weights={
            "search": 0.50, "view": 0.25, "click": 0.15,
            "add_to_cart": 0.03, "wishlist": 0.04,
            "coupon_view": 0.02, "checkout": 0.00, "purchase": 0.01,
        },
        middle_weights={
            "search": 0.20, "view": 0.30, "click": 0.22,
            "add_to_cart": 0.10, "wishlist": 0.12,
            "coupon_view": 0.04, "checkout": 0.01, "purchase": 0.01,
        },
        late_weights={
            "search": 0.15, "view": 0.18, "click": 0.10,
            "add_to_cart": 0.08, "wishlist": 0.20,
            "coupon_view": 0.10, "checkout": 0.08, "purchase": 0.11,
        },
    ),

    # ── category_browser ─────────────────────────────────────
    # Hành trình: Browse theo danh mục → Xem nhiều sản phẩm → Ít mua
    # EARLY : view + search theo category
    # MIDDLE: click + wishlist (so sánh sản phẩm)
    # LATE  : reengage hoặc mua nhẹ
    "category_browser": PersonaJourney(
        persona="category_browser",
        price_range=(50_000, 180_000),
        price_sensitivity="medium",
        next_best_action="reengage_catalog",
        early_weights={
            "search": 0.25, "view": 0.38, "click": 0.18,
            "add_to_cart": 0.06, "wishlist": 0.08,
            "coupon_view": 0.03, "checkout": 0.01, "purchase": 0.01,
        },
        middle_weights={
            "search": 0.12, "view": 0.28, "click": 0.22,
            "add_to_cart": 0.10, "wishlist": 0.18,
            "coupon_view": 0.05, "checkout": 0.03, "purchase": 0.02,
        },
        late_weights={
            "search": 0.10, "view": 0.15, "click": 0.12,
            "add_to_cart": 0.12, "wishlist": 0.10,
            "coupon_view": 0.05, "checkout": 0.16, "purchase": 0.20,
        },
    ),

    # ── deal_hunter ──────────────────────────────────────────
    # Hành trình: Tìm kiếm → Xem coupon NGAY → Cân nhắc → Mua nếu có deal
    # EARLY : search + coupon_view sớm (đặc trưng nhất của persona này)
    # MIDDLE: view + add_to_cart (đang so sánh giá)
    # LATE  : checkout nếu tìm được deal tốt
    "deal_hunter": PersonaJourney(
        persona="deal_hunter",
        price_range=(25_000, 110_000),
        price_sensitivity="high",
        next_best_action="push_coupon",
        early_weights={
            "search": 0.35, "view": 0.15, "click": 0.10,
            "add_to_cart": 0.05, "wishlist": 0.05,
            "coupon_view": 0.28, "checkout": 0.01, "purchase": 0.01,
        },
        middle_weights={
            "search": 0.18, "view": 0.22, "click": 0.14,
            "add_to_cart": 0.14, "wishlist": 0.10,
            "coupon_view": 0.14, "checkout": 0.05, "purchase": 0.03,
        },
        late_weights={
            "search": 0.10, "view": 0.15, "click": 0.10,
            "add_to_cart": 0.12, "wishlist": 0.08,
            "coupon_view": 0.12, "checkout": 0.18, "purchase": 0.15,
        },
    ),

    # ── loyal_member ─────────────────────────────────────────
    # Hành trình: Biết rõ muốn gì → add_to_cart NGAY → Checkout nhanh
    # EARLY : add_to_cart + view (ít search vì đã quen platform)
    # MIDDLE: checkout + purchase (quyết định nhanh)
    # LATE  : view thêm sản phẩm liên quan (mua thêm)
    "loyal_member": PersonaJourney(
        persona="loyal_member",
        price_range=(120_000, 320_000),
        price_sensitivity="low",
        next_best_action="upsell_membership",
        early_weights={
            "search": 0.08, "view": 0.20, "click": 0.15,
            "add_to_cart": 0.30, "wishlist": 0.08,
            "coupon_view": 0.05, "checkout": 0.10, "purchase": 0.04,
        },
        middle_weights={
            "search": 0.05, "view": 0.12, "click": 0.10,
            "add_to_cart": 0.18, "wishlist": 0.05,
            "coupon_view": 0.05, "checkout": 0.22, "purchase": 0.23,
        },
        late_weights={
            "search": 0.08, "view": 0.20, "click": 0.12,
            "add_to_cart": 0.12, "wishlist": 0.06,
            "coupon_view": 0.06, "checkout": 0.16, "purchase": 0.20,
        },
    ),

    # ── high_intent_buyer ─────────────────────────────────────
    # Hành trình: Search mục tiêu → add_to_cart NHANH → Checkout
    # EARLY : search + view + add_to_cart sớm (có chủ đích rõ)
    # MIDDLE: checkout + purchase (không do dự)
    # LATE  : view thêm để bundle
    "high_intent_buyer": PersonaJourney(
        persona="high_intent_buyer",
        price_range=(90_000, 260_000),
        price_sensitivity="medium",
        next_best_action="bundle_related_products",
        early_weights={
            "search": 0.22, "view": 0.20, "click": 0.15,
            "add_to_cart": 0.28, "wishlist": 0.05,
            "coupon_view": 0.04, "checkout": 0.04, "purchase": 0.02,
        },
        middle_weights={
            "search": 0.08, "view": 0.15, "click": 0.12,
            "add_to_cart": 0.20, "wishlist": 0.05,
            "coupon_view": 0.04, "checkout": 0.20, "purchase": 0.16,
        },
        late_weights={
            "search": 0.08, "view": 0.22, "click": 0.14,
            "add_to_cart": 0.14, "wishlist": 0.08,
            "coupon_view": 0.04, "checkout": 0.14, "purchase": 0.16,
        },
    ),
}


# ─────────────────────────────────────────────────────────────
# Sequence Noise (chỉ làm nhiễu thứ tự, không thay đổi tần suất)
# ─────────────────────────────────────────────────────────────
def apply_temporal_swap(
    sequence: list[str],
    rng: random.Random,
    swap_rate: float = 0.08,
) -> list[str]:
    """
    Hoán đổi 2 action ở xa nhau trong chuỗi (khoảng cách >= 5 bước).
    Không thay đổi tần suất action → MLP không bị ảnh hưởng.
    Làm xáo trộn thứ tự có ý nghĩa → LSTM bị ảnh hưởng một phần.

    Ví dụ: [search, view, coupon_view, add_to_cart, checkout, purchase]
    Sau swap: [search, checkout, coupon_view, add_to_cart, view, purchase]
    → MLP vẫn thấy cùng tần suất, LSTM nhận thấy checkout xuất hiện quá sớm
    """
    seq = list(sequence)
    n   = len(seq)
    for i in range(n):
        if rng.random() < swap_rate:
            # Chọn j cách xa ít nhất 5 bước
            candidates = [j for j in range(n) if abs(j - i) >= 5]
            if candidates:
                j = rng.choice(candidates)
                seq[i], seq[j] = seq[j], seq[i]
    return seq


def apply_phase_disruption(
    sequence: list[str],
    rng: random.Random,
    disrupt_rate: float = 0.12,
    segment_size: int = 5,
) -> list[str]:
    """
    Đảo ngược một đoạn dài (segment_size bước) trong chuỗi.
    Làm mờ ranh giới giữa các phase (EARLY/MIDDLE/LATE).
    LSTM nhạy cảm với sự thay đổi này vì nó mất đi tín hiệu
    về "đang ở phase nào trong hành trình mua hàng".

    Ví dụ đoạn EARLY bị đảo: [search, search, view, click, coupon_view]
    Thành: [coupon_view, click, view, search, search]
    → LSTM thấy coupon_view xuất hiện rất sớm, mất tín hiệu phase
    """
    seq = list(sequence)
    n   = len(seq)
    i   = 0
    while i < n - segment_size:
        if rng.random() < disrupt_rate:
            chunk = seq[i: i + segment_size]
            chunk.reverse()
            seq[i: i + segment_size] = chunk
            i += segment_size
        else:
            i += 1
    return seq


def apply_sequence_noise(
    sequence: list[str],
    rng: random.Random,
    temporal_swap_rate: float,
    phase_disrupt_rate: float,
) -> list[str]:
    """Áp dụng noise thứ tự theo thứ tự: swap trước, disrupt sau."""
    seq = apply_temporal_swap(sequence, rng, temporal_swap_rate)
    seq = apply_phase_disruption(seq, rng, phase_disrupt_rate)
    return seq


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    keys   = list(weights.keys())
    probs  = list(weights.values())
    return rng.choices(keys, weights=probs, k=1)[0]


def get_phase_weights(journey: PersonaJourney, step: int, total: int) -> dict[str, float]:
    """
    Trả về action_weights phù hợp với phase hiện tại trong chuỗi.
    EARLY : 30% đầu, MIDDLE: 40% giữa, LATE: 30% cuối.
    """
    ratio = step / max(total - 1, 1)
    if ratio < 0.30:
        return journey.early_weights
    elif ratio < 0.70:
        return journey.middle_weights
    else:
        return journey.late_weights


def generate_query(rng: random.Random, action: str, category_name: str, price: int) -> str:
    if action == "coupon_view":
        return rng.choice(["voucher", "sale", "coupon học tập", "khuyến mãi"])
    if action == "search":
        return rng.choice([
            f"{category_name.lower()} giá tốt",
            f"{category_name.lower()} cho học sinh",
            f"mua {category_name.lower()} online",
            f"{category_name.lower()} dưới {price // 1000}k",
        ])
    return ""


# ─────────────────────────────────────────────────────────────
# Main builder
# ─────────────────────────────────────────────────────────────
def build_dataset(
    out_path:               Path,
    user_count:             int                          = 2000,
    seed:                   int                          = 42,
    persona_distribution:   list[tuple[str, float]] | None = None,
    sequence_length_range:  tuple[int, int]              = (18, 42),
    dataset_label:          str                          = "base",
    temporal_swap_rate:     float                        = 0.08,
    phase_disrupt_rate:     float                        = 0.12,
) -> dict:
    """
    Sinh dataset hành vi người dùng dựa trên Journey Phase Model.

    Thiết kế cốt lõi:
    - Mỗi persona có 3 phase hành vi rõ ràng (EARLY / MIDDLE / LATE)
    - Action được chọn theo phase tương ứng → tạo tín hiệu thứ tự có ý nghĩa
    - Noise CHỈ làm xáo trộn thứ tự, không thay đổi tần suất action
    - MLP (mean pooling) không bị ảnh hưởng bởi noise thứ tự
    - LSTM/biLSTM học được pattern phase → phân hóa rõ hơn

    Args:
        temporal_swap_rate : Xác suất hoán đổi 2 action xa nhau (>= 5 bước).
        phase_disrupt_rate : Xác suất đảo một đoạn 5 action liên tiếp.
    """
    if persona_distribution is None:
        persona_distribution = [
            ("new_explorer",      0.20),
            ("category_browser",  0.24),
            ("deal_hunter",       0.20),
            ("loyal_member",      0.16),
            ("high_intent_buyer", 0.20),
        ]

    rng             = random.Random(seed)
    start           = datetime(2026, 1, 1, 8, 0, 0)
    rows:           list[dict]            = []
    persona_counts: defaultdict[str, int] = defaultdict(int)

    persona_labels  = [name   for name, _      in persona_distribution]
    persona_weights = [weight for _,    weight in persona_distribution]

    for user_id in range(1, user_count + 1):
        persona  = rng.choices(persona_labels, weights=persona_weights, k=1)[0]
        persona_counts[persona] += 1
        journey  = JOURNEYS[persona]

        base_category   = rng.choice(CATEGORIES)
        sequence_length = rng.randint(*sequence_length_range)
        event_time      = start + timedelta(hours=rng.randint(0, 24 * 45))
        session_index   = 1
        purchase_count  = 0

        # ── Sinh chuỗi action theo phase ──────────────────────
        raw_sequence: list[str] = []
        for step in range(sequence_length):
            phase_weights = get_phase_weights(journey, step, sequence_length)
            action        = weighted_choice(rng, phase_weights)

            # Ràng buộc thực tế
            if action in {"checkout", "purchase"} and step < 3:
                action = rng.choice(["search", "view", "click"])
            if action == "purchase":
                purchase_count += 1
            if action == "purchase" and purchase_count > 3:
                action = rng.choice(["view", "add_to_cart", "checkout"])

            raw_sequence.append(action)

        # ── Áp dụng noise thứ tự ──────────────────────────────
        noisy_sequence = apply_sequence_noise(
            sequence=raw_sequence,
            rng=rng,
            temporal_swap_rate=temporal_swap_rate,
            phase_disrupt_rate=phase_disrupt_rate,
        )

        # ── Ghi từng bước ra CSV ──────────────────────────────
        for step_idx, action in enumerate(noisy_sequence):
            category_name = base_category if rng.random() < 0.65 else rng.choice(CATEGORIES)
            price         = rng.randint(*journey.price_range)
            quantity      = 1 if action != "purchase" else rng.randint(1, 2)
            query         = generate_query(rng, action, category_name, price)

            rows.append({
                "user_id":           user_id,
                "session_id":        f"S{user_id:04d}-{session_index:02d}",
                "step":              step_idx + 1,
                "timestamp":         event_time.isoformat(),
                "product_id":        rng.randint(1000, 1300),
                "category_name":     category_name,
                "action":            action,
                "price":             price,
                "quantity":          quantity,
                "query":             query,
                "persona_label":     persona,
                "next_best_action":  journey.next_best_action,
                "price_sensitivity": journey.price_sensitivity,
            })

            event_time += timedelta(minutes=rng.randint(2, 45))
            if rng.random() < 0.12:
                session_index += 1
                event_time += timedelta(hours=rng.randint(4, 36))

    # ── Ghi file ──────────────────────────────────────────────
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "dataset":               dataset_label,
        "path":                  str(out_path),
        "total_users":           user_count,
        "total_rows":            len(rows),
        "avg_sequence_length":   round(len(rows) / user_count, 1),
        "sequence_length_range": sequence_length_range,
        "persona_counts":        dict(sorted(persona_counts.items())),
        "noise_config": {
            "temporal_swap_rate":  temporal_swap_rate,
            "phase_disrupt_rate":  phase_disrupt_rate,
        },
    }


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent / "data"

    # Dataset 1 — Baseline
    stats1 = build_dataset(
        out_path=base_dir / "dataset1_baseline.csv",
        user_count=2000, seed=42,
        persona_distribution=[
            ("new_explorer",      0.20), ("category_browser", 0.24),
            ("deal_hunter",       0.20), ("loyal_member",      0.16),
            ("high_intent_buyer", 0.20),
        ],
        sequence_length_range=(18, 42),
        dataset_label="Dataset 1 — Baseline (Balanced)",
        temporal_swap_rate=0.08,
        phase_disrupt_rate=0.12,
    )

    # Dataset 2 — Flash Sale
    stats2 = build_dataset(
        out_path=base_dir / "dataset2_flash_sale.csv",
        user_count=2000, seed=123,
        persona_distribution=[
            ("new_explorer",      0.10), ("category_browser", 0.15),
            ("deal_hunter",       0.38), ("loyal_member",      0.22),
            ("high_intent_buyer", 0.15),
        ],
        sequence_length_range=(22, 55),
        dataset_label="Dataset 2 — Flash Sale Season",
        temporal_swap_rate=0.10,   # Cao hơn: hành vi mùa sale ít nhất quán
        phase_disrupt_rate=0.15,
    )

    # Dataset 3 — Cold Start
    stats3 = build_dataset(
        out_path=base_dir / "dataset3_cold_start.csv",
        user_count=2000, seed=777,
        persona_distribution=[
            ("new_explorer",      0.55), ("category_browser", 0.25),
            ("deal_hunter",       0.08), ("loyal_member",      0.04),
            ("high_intent_buyer", 0.08),
        ],
        sequence_length_range=(5, 18),
        dataset_label="Dataset 3 — Cold Start / New User Heavy",
        temporal_swap_rate=0.05,   # Thấp hơn: sequence ngắn, giữ tín hiệu
        phase_disrupt_rate=0.06,
    )

    # Print summary
    print("\n" + "=" * 65)
    print("DATASET GENERATION COMPLETE")
    print("=" * 65)
    for stats in [stats1, stats2, stats3]:
        print(f"\n📦 {stats['dataset']}")
        print(f"   Path             : {stats['path']}")
        print(f"   Users            : {stats['total_users']}")
        print(f"   Total rows       : {stats['total_rows']}")
        print(f"   Avg seq length   : {stats['avg_sequence_length']} steps")
        print(f"   Seq range        : {stats['sequence_length_range']}")
        print(f"   Noise            : swap={stats['noise_config']['temporal_swap_rate']}"
              f"  disrupt={stats['noise_config']['phase_disrupt_rate']}")
        print(f"   Persona counts   :")
        for persona, count in stats['persona_counts'].items():
            pct = round(count / stats['total_users'] * 100, 1)
            print(f"      {persona:<22} {count:>4} users  ({pct:>5}%)")
    print("\n" + "=" * 65)