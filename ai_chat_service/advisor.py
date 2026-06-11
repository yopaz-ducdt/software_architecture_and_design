from __future__ import annotations

import re
import unicodedata
from typing import Any

from behavior_model import BehaviorModel
from sequence_behavior_model import SequenceBehaviorModel
from data_fetcher import ServiceClient
from graph_store import GraphKBStore
from kb_store import KBStore
from llm_service import LLMService

CATEGORY_ALIASES = {
    "Sách": ["sach", "book", "truyen", "self help", "tieu thuyet", "fantasy"],
    "Dụng cụ học tập": [
        "dung cu hoc tap",
        "but",
        "vo",
        "so",
        "stationery",
        "highlight",
        "sotay",
        "so tay",
        "sổ tay",
        "di hoc",
        "đi học",
        "hoc",
        "học",
        "ghi chu",
        "ghi chú",
        "viet",
        "viết",
        "notebook",
        "thuoc ke",
        "thước kẻ",
    ],
    "Đồ chơi": ["do choi", "lego", "toy", "xep hinh"],
    "Gói quà": ["goi qua", "quà", "qua", "gift", "combo", "qua tang", "set qua tang", "set quà tặng", "sinh nhat", "ky niem", "dip", "tang ban", "tang nguoi yeu"],
    "Ba lô": ["ba lo", "balo", "backpack", "cap", "tui di hoc", "cap sach", "cặp sách"],
    "Bình nước": ["binh nuoc", "binh giu nhiet", "water bottle", "locknlock"],
    "Đồ điện tử học tập": [
        "do dien tu hoc tap",
        "may tinh",
        "calculator",
        "study tech",
        "dong ho",
        "đồng hồ",
        "dongho",
        "xem gio",
        "xem giờ",
        "watch",
        "sac du phong",
        "sạc dự phòng",
        "cap sac",
        "cáp sạc",
        "cuc sac",
        "cục sạc",
        "chuot",
        "chuột",
    ],
    "Mỹ thuật": ["my thuat", "ve", "chi mau", "art", "thu cong"],
    "Đồ trang trí bàn học": ["do trang tri ban hoc", "den ban", "desk decor", "goc hoc tap", "ban", "bàn", "ghe", "ghế"],
    "Đồ lưu niệm": ["do luu niem", "moc khoa", "souvenir", "qua nho", "capybara", "sinh nhat", "ky niem", "dip"],
    "Đồ ăn vặt": ["do an vat", "đồ ăn vặt", "banh", "bánh", "keo", "kẹo", "snack", "do an"],
    "Chăm sóc cá nhân": ["cham soc ca nhan", "chăm sóc cá nhân", "may cao rau", "máy cạo râu", "skincare", "kem chong nang", "sua rua mat"],
}

POLICY_KEYWORDS = [
    "don hang",
    "van chuyen",
    "giao hang",
    "shipping",
    "refund",
    "doi tra",
    "coupon",
    "voucher",
    "thanh vien",
    "membership",
    "cart",
    "gio hang",
    "checkout",
    "thanh toan",
    "payment",
]

PRODUCT_KEYWORDS = [
    "goi y",
    "nen mua",
    "ngan sach",
    "bao nhieu",
    "mua gi",
    "san pham",
    "danh muc",
    # "qua" đã bỏ — quá mơ hồ, khớp nhầm với "buồn quá", "mệt quá"
    "goi qua",
    "qua tang",
    "do dung",
    "phu kien",
    "xem gio",
    "xem giờ",
    "watch",
    "so tay",
    "sổ tay",
    "notebook",
    "di hoc",
    "đi học",
    "hoc tap",
    "học tập",
    "ghi chu",
    "ghi chú",
    "viet",
    "viết",
    "sinh nhat",
    "ky niem",
    "dip",
    "tang ban",
    "tang nguoi yeu",
    "sac du phong",
    "may cao rau",
    "do an vat",
    "cap sac",
    "cuc sac",
    "chuot",
    "thuoc ke",
    "cap sach",
    "ban hoc",
    "ghe",
    "banh",
    "keo",
]

PURCHASE_KEYWORDS = ["mua", "muon mua", "dat mua", "can mua", "tim mua", "chot", "lay", "can", "cần"]
AVAILABILITY_KEYWORDS = ["co ban", "shop co", "cua hang co", "ben minh co", "co khong"]

GREETING_KEYWORDS = [
    "hello", "hi", "hey", "xin chao", "chao ban", "chao shop", "chao", "alo",
    "good morning", "good afternoon", "good evening", "howdy",
]

EMOTIONAL_KEYWORDS = [
    # Buồn / tiêu cực — dùng từ đủ dài để tránh khớp nhầm substring
    "buon",         # đủ dài, an toàn
    "buon qua",
    "chan nan",
    "met moi",
    "met moi qua",
    "qua met",
    "stress",
    "lo lang",
    "lo au",
    "kho chiu",
    "that vong",
    "tuc gian",
    "khoc",
    "co don",
    "tram cam",
    "buon ngu",
    "khong vui",
    "toi buon",
    "minh buon",
    "dang buon",
    "sad",
    "depressed",
    "lonely",
    "angry",
    # Vui / tích cực
    "vui qua",
    "vui lam",
    "phan khich",
    "hanh phuc",
    "tuyet voi",
    "excited",
    "happy",
    "hom nay vui",
    "hom nay tot",
    "hom nay dep",
]


def _searchable_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def parse_money_to_vnd(text: str) -> dict[str, int | str] | None:
    normalized = (
        _searchable_text(text)
        .replace("trieu", "000000")
        .replace("nghin", "000")
        .replace("ngan", "000")
        .replace("k", "000")
    )
    nums = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:[\.,]\d+)?", normalized)]
    if not nums:
        return None

    def normalize(value: float) -> int:
        return int(value * 1000) if value < 1000 and "000" in normalized else int(value)

    if re.search(r"(tu|range|khoang)\s*\d+.*(den|-|toi)\s*\d+", normalized) and len(nums) >= 2:
        low, high = normalize(nums[0]), normalize(nums[1])
        return {"type": "range", "min": min(low, high), "max": max(low, high)}
    if any(keyword in normalized for keyword in ["duoi", "khong qua", "toi da", "under", "below"]):
        return {"type": "max", "value": normalize(nums[0])}
    if any(keyword in normalized for keyword in ["tren", "it nhat", "tro len", "at least", "from"]):
        return {"type": "min", "value": normalize(nums[0])}
    return {"type": "approx", "value": normalize(nums[0])}


def match_budget(price: float, budget: dict[str, int | str] | None) -> bool:
    if not budget:
        return True
    if budget["type"] == "min":
        return price >= int(budget["value"])
    if budget["type"] == "max":
        return price <= int(budget["value"])
    if budget["type"] == "range":
        return int(budget["min"]) <= price <= int(budget["max"])
    return abs(price - int(budget["value"])) <= 30000


def detect_categories(question: str, preferred_categories: list[str]) -> list[str]:
    q = _searchable_text(question)
    hits = [category for category, aliases in CATEGORY_ALIASES.items() if any(alias in q for alias in aliases)]
    if not hits:
        hits.extend(preferred_categories[:3])
    return list(dict.fromkeys(hits))


def detect_categories_strict(question: str) -> list[str]:
    q = _searchable_text(question)
    hits = [category for category, aliases in CATEGORY_ALIASES.items() if any(alias in q for alias in aliases)]
    return list(dict.fromkeys(hits))


def classify_intent(question: str) -> str:
    q = _searchable_text(question)
    q_tokens = q.split()
    # 1. Greeting — chỉ khi câu ngắn (≤5 từ) để tránh nhầm
    if len(q_tokens) <= 5 and any(keyword in q for keyword in GREETING_KEYWORDS):
        return "greeting"
    # 2. Emotional — kiểm tra TRƯỚC purchase/product vì nhiều từ cảm xúc là substring
    #    (ví dụ: "buồn quá" có "qua" từng nằm trong PRODUCT_KEYWORDS)
    if any(keyword in q for keyword in EMOTIONAL_KEYWORDS):
        return "emotional"
    # 3. Các intent mua hàng / chính sách
    if any(keyword in q for keyword in AVAILABILITY_KEYWORDS):
        return "availability_query"
    if any(keyword in q for keyword in PURCHASE_KEYWORDS):
        return "purchase_request"
    if any(keyword in q for keyword in POLICY_KEYWORDS):
        return "policy"
    if any(keyword in q for keyword in PRODUCT_KEYWORDS) or detect_categories_strict(question):
        return "product_recommendation"
    return "general"


def find_explicit_product(question: str, products: list[dict[str, Any]]) -> dict[str, Any] | None:
    q_norm = _searchable_text(question)
    if not q_norm:
        return None

    matches: list[tuple[float, dict[str, Any]]] = []
    for product in products:
        title = str(product.get("title") or product.get("name") or "").strip()
        sku = str(product.get("sku") or "").strip()
        if not title:
            continue
        title_norm = _searchable_text(title)
        sku_norm = _searchable_text(sku)
        score = 0.0
        if title_norm and title_norm in q_norm:
            score = 10.0 + len(title_norm) / 100
        elif sku_norm and sku_norm in q_norm:
            score = 9.0
        else:
            tokens = [token for token in title_norm.split() if len(token) >= 3]
            hits = sum(1 for token in tokens if token in q_norm)
            if tokens:
                coverage = hits / len(tokens)
                if hits >= 2 or coverage >= 0.6:
                    score = 5.0 + coverage
        if score > 0:
            matches.append((score, product))

    if not matches:
        return None
    matches.sort(key=lambda item: (-item[0], float(item[1].get("price", 0) or 0)))
    return matches[0][1]


def _product_text(product: dict[str, Any]) -> str:
    parts = [
        str(product.get("title") or product.get("name") or ""),
        str(product.get("description") or ""),
        str(product.get("category_name") or ""),
        str(product.get("author_name") or ""),
        str(product.get("brand_name") or ""),
    ]
    return _searchable_text(" ".join(parts))


class MarketplaceAdvisor:
    def __init__(self, base_dir: str):
        self.services = ServiceClient()
        self.behavior_model = BehaviorModel(base_dir)
        self.sequence_behavior_model = SequenceBehaviorModel(base_dir)
        self.kb = KBStore(base_dir)
        self.graph = GraphKBStore(base_dir)
        self.llm = LLMService()

    def _category_name(self, product: dict[str, Any], category_lookup: dict[Any, str]) -> str:
        return str(product.get("category_name") or category_lookup.get(product.get("category_id")) or "Khác")

    def _category_label(self, category_name: str | None) -> str:
        if not category_name:
            return "sản phẩm"
        special_labels = {
            "Sách": "sách",
            "Dụng cụ học tập": "dụng cụ học tập",
            "Đồ chơi": "đồ chơi",
            "Gói quà": "gói quà",
            "Ba lô": "ba lô",
            "Bình nước": "bình nước",
            "Đồ điện tử học tập": "đồ điện tử học tập",
            "Mỹ thuật": "đồ mỹ thuật",
            "Đồ trang trí bàn học": "đồ trang trí bàn học",
            "Đồ lưu niệm": "đồ lưu niệm",
        }
        return special_labels.get(category_name, category_name.lower())

    def _score_products(
        self,
        products: list[dict[str, Any]],
        categories: list[dict[str, Any]],
        snapshot: dict[str, Any],
        question: str,
        forced_categories: list[str] | None = None,
        graph_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        budget = parse_money_to_vnd(question)
        preferred = forced_categories or detect_categories(question, snapshot.get("preferred_categories", []))
        category_lookup = {item.get("id"): item.get("name") for item in categories}
        behavior = snapshot["behavior"]
        recent_search_terms = snapshot.get("recent_search_terms", [])
        recent_viewed_product_ids = set(snapshot.get("recent_viewed_product_ids", []))
        recent_viewed_categories = set(snapshot.get("recent_viewed_categories", []))
        graph_context = graph_context or {}
        graph_product_ids = set(graph_context.get("recent_product_ids", [])) | set(graph_context.get("query_product_ids", []))
        graph_categories = set(graph_context.get("preferred_categories", []))
        graph_brands = set(graph_context.get("preferred_brands", []))
        graph_types = set(graph_context.get("preferred_product_types", []))

        scoped_products = products
        if forced_categories:
            scoped_products = [p for p in products if self._category_name(p, category_lookup) in forced_categories]

        filtered = [p for p in scoped_products if match_budget(float(p.get("price", 0) or 0), budget)]
        candidates = filtered or scoped_products or products
        ranked: list[dict[str, Any]] = []

        for product in candidates:
            price = float(product.get("price", 0) or 0)
            stock = int(product.get("stock_quantity", 0) or 0)
            category_name = self._category_name(product, category_lookup)
            product_id = product.get("id")
            brand_name = str(product.get("brand_name") or "")
            product_type_name = str(product.get("product_type_name") or "")
            product_text = _product_text(product)
            score = 0.0
            reasons: list[str] = []

            if preferred and category_name in preferred:
                score += 3.0
                reasons.append(f"khớp nhóm quan tâm: {category_name}")
            if category_name in graph_categories:
                score += 2.4
                reasons.append("khớp hành vi trên graph")
            if category_name in recent_viewed_categories:
                score += 1.8
                reasons.append("cùng nhóm với sản phẩm vừa xem")
            if product_id in graph_product_ids:
                score += 2.8
                reasons.append("liên kết mạnh trên graph")
            if brand_name and brand_name in graph_brands:
                score += 1.6
                reasons.append(f"khớp brand quan tâm: {brand_name}")
            if product_type_name and product_type_name in graph_types:
                score += 1.4
                reasons.append(f"khớp loại sản phẩm: {product_type_name}")
            if budget:
                if budget["type"] == "approx":
                    score += max(0.0, 2.5 - abs(price - int(budget["value"])) / 25000)
                else:
                    score += 2.0
                    reasons.append("nằm trong ngân sách")
            for term in recent_search_terms[-5:]:
                term_tokens = [token for token in _searchable_text(term).split() if len(token) >= 3]
                if term_tokens and any(token in product_text for token in term_tokens):
                    score += 2.2
                    reasons.append(f"khớp tìm kiếm gần đây: {term}")
                    break
            if behavior.price_sensitivity == "high" and price <= 150000:
                score += 1.8
                reasons.append("mức giá mềm")
            if behavior.purchase_intent >= 0.65 and stock > 0:
                score += 1.2
                reasons.append("có sẵn hàng")
            if product_id in recent_viewed_product_ids:
                score -= 1.5
            if stock <= 0:
                score -= 5.0
            score += min(stock / 100, 1.0)

            ranked.append(
                {
                    "product": product,
                    "score": round(score, 3),
                    "category_name": category_name,
                    "reasons": reasons,
                }
            )

        ranked.sort(key=lambda item: (-item["score"], float(item["product"].get("price", 0) or 0)))
        return ranked

    def _format_kb_advice(self, kb_hits: list, min_score: float = 0.05) -> str:
        """Trích xuất lời khuyên hữu ích từ Knowledge Base nếu có kết quả đủ liên quan."""
        relevant = [hit for hit in kb_hits if hit.score >= min_score and hit.content.strip()]
        if not relevant:
            return ""
        lines = ["\n💡 Lời khuyên thêm:"]
        for hit in relevant[:2]:
            content = hit.content.strip()
            # Lấy tối đa 2 dòng đầu của content để tóm tắt ngắn gọn
            preview_lines = [line.strip() for line in content.splitlines() if line.strip()][:3]
            preview = " ".join(preview_lines)
            if len(preview) > 200:
                preview = preview[:200].rsplit(" ", 1)[0] + "..."
            lines.append(f"- {preview}")
        return "\n".join(lines)

    def _format_general_answer(
        self,
        user_name: str,
        question: str,
        kb_hits: list,
        top_products: list[dict[str, Any]],
        preferred: list[str],
        graph_context: dict[str, Any],
        behavior: Any,
        snapshot: dict[str, Any],
    ) -> str:
        """Xử lý câu hỏi chung: dùng KB để trả lời nội dung + gợi ý sản phẩm từ shop."""
        lines = [f"Mình đang tư vấn cho {user_name}.", ""]

        # Phần 1: Trả lời từ KB nếu có nội dung liên quan
        relevant_hits = [hit for hit in kb_hits if hit.score >= 0.05 and hit.content.strip()]
        if relevant_hits:
            lines.append("📖 Thông tin hữu ích:")
            for hit in relevant_hits[:2]:
                content = hit.content.strip()
                preview_lines = [line.strip() for line in content.splitlines() if line.strip()][:4]
                preview = "\n  ".join(preview_lines)
                lines.append(f"• {hit.title}:\n  {preview}")
            lines.append("")
        else:
            lines.append(
                "Mình có thể gợi ý sản phẩm theo ngân sách hoặc danh mục, đồng thời hỗ trợ "
                "các câu hỏi về coupon, thành viên, vận chuyển, giỏ hàng, thanh toán và đổi trả."
            )
            lines.append("")

        # Phần 2: Gợi ý sản phẩm phù hợp từ shop
        if top_products:
            lines.append("🛍️ Sản phẩm gợi ý từ shop cho bạn:")
            for idx, item in enumerate(top_products[:3], start=1):
                product = item["product"]
                title = product.get("title") or product.get("name") or "Sản phẩm"
                price = int(float(product.get("price", 0) or 0))
                stock = int(product.get("stock_quantity", 0) or 0)
                reasons = item["reasons"][:1] or ["phù hợp nhu cầu hiện tại"]
                stock_label = "còn hàng" if stock > 0 else "tạm hết"
                lines.append(f"{idx}. {title} - {price:,}đ ({stock_label}) — {reasons[0]}")
            lines.append("")

        if preferred:
            lines.append(f"Gần đây bạn đang quan tâm nhiều đến: {', '.join(preferred[:3])}.")

        return "\n".join(lines)

    def _dynamic_context(self, snapshot: dict[str, Any]) -> str:
        marketing = snapshot.get("marketing", {})
        cart_summary = snapshot.get("cart_summary", {})
        lines: list[str] = []
        if cart_summary.get("item_count"):
            lines.append(
                f"- Giỏ hàng hiện có {cart_summary.get('item_count')} sản phẩm, tạm tính {int(cart_summary.get('total_price', 0)):,}đ."
            )
        for coupon in marketing.get("coupons", [])[:3]:
            if coupon.get("active", True):
                discount = coupon.get("discount_percent") or coupon.get("discount_amount")
                lines.append(f"- {coupon.get('code')}: giảm {discount} với đơn tối thiểu {int(coupon.get('min_order_value', 0)):,}đ")
        for tier in marketing.get("tiers", [])[:2]:
            if tier.get("free_shipping"):
                lines.append(f"- Hạng {tier.get('name')} có giảm {tier.get('discount_percent', 0)}% và hỗ trợ miễn phí ship.")
        return "\n".join(lines)

    def _format_purchase_answer(
        self,
        user_name: str,
        product: dict[str, Any],
        category_name: str,
        behavior: Any,
        snapshot: dict[str, Any],
    ) -> str:
        title = product.get("title") or product.get("name") or "Sản phẩm"
        price = int(float(product.get("price", 0) or 0))
        stock = int(product.get("stock_quantity", 0) or 0)
        description = product.get("description") or "Sản phẩm đang có trong catalog hiện tại."
        cart_summary = snapshot.get("cart_summary", {})
        stock_line = f"Còn hàng ({stock} sản phẩm khả dụng)." if stock > 0 else "Tạm hết hàng."
        next_action = "Bạn có thể thêm ngay sản phẩm này vào giỏ hàng từ trang chi tiết."
        if behavior.next_best_action == "push_coupon":
            dynamic = self._dynamic_context(snapshot)
            if dynamic:
                next_action = f"Bạn nên kiểm tra ưu đãi trước khi chốt đơn:\n{dynamic}"
        elif cart_summary.get("item_count"):
            next_action = (
                f"Giỏ hàng hiện có {cart_summary.get('item_count')} sản phẩm, "
                "bạn có thể vào checkout để chốt cùng đơn."
            )
        return "\n".join(
            [
                f"Mình đã tìm thấy sản phẩm phù hợp cho {user_name}.",
                "",
                f"Tên sản phẩm: {title}",
                f"Danh mục: {category_name}",
                f"Giá hiện tại: {price:,}đ",
                f"Tình trạng: {stock_line}",
                f"Mô tả ngắn: {description}",
                f"Gợi ý tiếp theo: {next_action}",
            ]
        )

    def _format_category_purchase_answer(
        self,
        user_name: str,
        category_name: str,
        ranked_products: list[dict[str, Any]],
        snapshot: dict[str, Any],
    ) -> str:
        lines = [
            f"Mình đã tìm thấy nhóm sản phẩm phù hợp cho {user_name}.",
            "",
            f"Nhóm sản phẩm: {category_name}",
            "Các lựa chọn phù hợp nhất:",
        ]
        for idx, item in enumerate(ranked_products[:3], start=1):
            product = item["product"]
            title = product.get("title") or product.get("name") or "Sản phẩm"
            price = int(float(product.get("price", 0) or 0))
            stock = int(product.get("stock_quantity", 0) or 0)
            reasons = item["reasons"][:2] or ["phù hợp với nhu cầu hiện tại"]
            lines.append(
                f"{idx}. {title} - {price:,}đ\n"
                f"   - Tồn kho: {'Còn hàng' if stock > 0 else 'Tạm hết hàng'}\n"
                f"   - Lý do: {'; '.join(reasons)}"
            )
        dynamic = self._dynamic_context(snapshot)
        if dynamic:
            lines.append("\nNgữ cảnh mua sắm hiện tại:")
            lines.append(dynamic)
        lines.append("\nNếu bạn muốn, mình có thể lọc tiếp theo ngân sách hoặc chọn ra 1 sản phẩm nổi bật nhất trong nhóm này.")
        return "\n".join(lines)

    def _format_availability_answer(
        self,
        user_name: str,
        product: dict[str, Any] | None,
        category_name: str | None,
        matched_products: list[dict[str, Any]],
    ) -> str:
        if product:
            title = product.get("title") or product.get("name") or "Sản phẩm"
            price = int(float(product.get("price", 0) or 0))
            stock = int(product.get("stock_quantity", 0) or 0)
            status = "Còn hàng" if stock > 0 else "Tạm hết hàng"
            return "\n".join(
                [
                    f"Có, shop hiện có {title}.",
                    f"Danh mục: {category_name or 'Khác'}",
                    f"Giá hiện tại: {price:,}đ",
                    f"Tình trạng: {status}",
                    "Nếu bạn muốn, mình có thể gợi ý thêm các lựa chọn cùng nhóm hoặc cùng tầm giá.",
                ]
            )

        if category_name and matched_products:
            category_label = self._category_label(category_name)
            lines = [
                f"Có, shop hiện có bán {category_label}.",
                "",
                f"Một vài sản phẩm thuộc {category_label}:",
            ]
            for idx, item in enumerate(matched_products[:3], start=1):
                title = item.get("title") or item.get("name") or "Sản phẩm"
                price = int(float(item.get("price", 0) or 0))
                stock = int(item.get("stock_quantity", 0) or 0)
                lines.append(f"{idx}. {title} - {price:,}đ - {'Còn hàng' if stock > 0 else 'Tạm hết hàng'}")
            lines.append("")
            lines.append(f"Nếu bạn muốn, mình có thể lọc tiếp theo tầm giá hoặc chọn mẫu phù hợp nhất trong phần {category_label}.")
            return "\n".join(lines)

        return (
            f"Hiện mình chưa thấy sản phẩm phù hợp đúng với yêu cầu của {user_name}. "
            "Bạn thử gửi tên sản phẩm hoặc nhóm cụ thể hơn để mình kiểm tra lại."
        )

    def answer(self, customer_id: int, question: str, user_name: str = "Khách hàng") -> dict[str, Any]:
        snapshot = self.services.get_user_snapshot(customer_id)
        base_behavior = self.behavior_model.predict(snapshot.get("feature_values", {}))
        sequence_behavior = self.sequence_behavior_model.predict(snapshot)
        behavior = sequence_behavior if sequence_behavior.used_sequence_model else base_behavior
        snapshot["behavior"] = behavior
        snapshot["behavior_fallback"] = base_behavior

        intent = classify_intent(question)
        kb_hits = self.kb.search(question, top_k=4)
        categories = snapshot.get("categories", [])
        products = snapshot.get("products", [])
        explicit_product = find_explicit_product(question, products)
        preferred = snapshot.get("preferred_categories", [])
        strict_categories = detect_categories_strict(question)
        category_lookup = {item.get("id"): item.get("name") for item in categories}
        graph_context = self.graph.get_context(customer_id, question, top_k=6)
        
        # Lọc các sản phẩm phù hợp nhất để gửi làm context cho LLM
        scoped_products = []
        if explicit_product:
            scoped_products = [explicit_product]
        elif strict_categories:
            category_ranked = self._score_products(
                products,
                categories,
                snapshot,
                question,
                forced_categories=strict_categories,
                graph_context=graph_context,
            )[:3]
            scoped_products = [item["product"] for item in category_ranked]
        else:
            top_scored = self._score_products(products, categories, snapshot, question, graph_context=graph_context)[:3]
            scoped_products = [item["product"] for item in top_scored]
            
        dynamic = self._dynamic_context(snapshot)
        
        # Gom context và gọi LLM
        prompt = self.llm.build_prompt(
            user_name=user_name,
            question=question,
            behavior=behavior.__dict__,
            products=scoped_products,
            kb_docs=[hit.content for hit in kb_hits],
            dynamic_context=dynamic
        )
        
        llm_answer = self.llm.generate_answer(prompt)
        
        return {
            "answer": llm_answer,
            "top_products": scoped_products,
            "kb_hits": [hit.__dict__ for hit in kb_hits],
            "behavior": behavior.__dict__,
            "graph_context": graph_context,
        }

    def recommend(self, customer_id: int, user_name: str = "Khách hàng", limit: int = 6) -> dict[str, Any]:
        snapshot = self.services.get_user_snapshot(customer_id)
        base_behavior = self.behavior_model.predict(snapshot.get("feature_values", {}))
        sequence_behavior = self.sequence_behavior_model.predict(snapshot)
        behavior = sequence_behavior if sequence_behavior.used_sequence_model else base_behavior
        snapshot["behavior"] = behavior
        snapshot["behavior_fallback"] = base_behavior

        recent_search_terms = snapshot.get("recent_search_terms", [])
        preferred_categories = snapshot.get("preferred_categories", [])
        synthetic_question = " ".join(recent_search_terms[-3:] + preferred_categories[:2]).strip() or "goi y san pham phu hop"
        graph_context = self.graph.get_context(customer_id, synthetic_question, top_k=max(limit, 6))
        ranked = self._score_products(
            snapshot.get("products", []),
            snapshot.get("categories", []),
            snapshot,
            synthetic_question,
            graph_context=graph_context,
        )
        picks = ranked[:limit]

        reasons: list[str] = []
        if recent_search_terms:
            reasons.append(f"dựa trên tìm kiếm gần đây: {', '.join(recent_search_terms[-3:])}")
        if preferred_categories:
            reasons.append(f"ưu tiên danh mục: {', '.join(preferred_categories[:3])}")
        if graph_context.get("preferred_categories"):
            reasons.append(f"graph quan tâm mạnh: {', '.join(graph_context['preferred_categories'][:3])}")
        if not reasons:
            reasons.append("dựa trên hành vi mua sắm gần đây")

        return {
            "title": f"Gợi ý cho {user_name}",
            "summary": "; ".join(reasons),
            "products": [item["product"] for item in picks],
            "behavior": behavior.__dict__,
            "graph_context": graph_context,
        }
