from __future__ import annotations

DEFAULT_CATEGORIES = [
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
    {"name": "Đồ ăn vặt", "slug": "snacks", "description": "Đồ ăn nhẹ, bánh kẹo giải lao."},
    {"name": "Chăm sóc cá nhân", "slug": "personal-care", "description": "Sản phẩm chăm sóc sức khoẻ và làm đẹp cơ bản."},
]

DEFAULT_PRODUCT_TYPES = [
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
    {"name": "Snack", "slug": "snack", "description": "Snacks and quick bites."},
    {"name": "Personal Care", "slug": "personal-care", "description": "Personal care and grooming items."},
]

# ─────────────────────────────────────────────────────────────
# Dữ liệu gốc từ seed_products_bulk.py (dùng để generate fallback)
# ─────────────────────────────────────────────────────────────
_CATEGORY_META = {
    "books":         {"name": "Sách",                  "type": "book",        "prices": (79000,  249000, 30000)},
    "stationery":    {"name": "Dụng cụ học tập",       "type": "stationery",  "prices": (19000,   99000, 10000)},
    "toys":          {"name": "Đồ chơi",               "type": "toy",         "prices": (99000,  549000, 50000)},
    "gift-packs":    {"name": "Gói quà",               "type": "gift-pack",   "prices": (99000,  259000, 30000)},
    "backpacks":     {"name": "Ba lô",                 "type": "backpack",    "prices": (249000, 599000, 50000)},
    "water-bottles": {"name": "Bình nước",             "type": "bottle",      "prices": (99000,  299000, 25000)},
    "study-tech":    {"name": "Đồ điện tử học tập",   "type": "study-tech",  "prices": (199000, 799000, 50000)},
    "art-supplies":  {"name": "Mỹ thuật",              "type": "art-supply",  "prices": (59000,  299000, 30000)},
    "desk-decor":    {"name": "Đồ trang trí bàn học", "type": "desk-decor",  "prices": (79000,  399000, 40000)},
    "souvenirs":     {"name": "Đồ lưu niệm",          "type": "souvenir",    "prices": (49000,  159000, 20000)},
    "snacks":        {"name": "Đồ ăn vặt",            "type": "snack",       "prices": (10000,  80000,  10000)},
    "personal-care": {"name": "Chăm sóc cá nhân",     "type": "personal-care","prices": (50000, 350000, 30000)},
}

_TEMPLATES = {
    "books":         ["Sách kỹ năng {w}", "Combo sách {w}", "Sách học {w}", "Tuyển tập {w}"],
    "stationery":    ["Sổ tay {w}", "Bút gel {w}", "Set văn phòng {w}", "Giấy note {w}", "Thước kẻ {w}"],
    "toys":          ["Đồ chơi {w}", "Bộ xếp hình {w}", "Robot {w}", "Đồ chơi giáo dục {w}"],
    "gift-packs":    ["Gói quà {w}", "Set quà tặng {w}", "Combo quà {w}", "Hộp quà {w}"],
    "backpacks":     ["Ba lô {w}", "Túi xách {w}", "Balo học {w}", "Balo du lịch {w}", "Cặp sách {w}"],
    "water-bottles": ["Bình nước {w}", "Bình giữ nhiệt {w}", "Bình thể thao {w}", "Bình du lịch {w}"],
    "study-tech":    ["Đèn học {w}", "Tai nghe {w}", "Chuột máy tính {w}", "Bàn phím mini {w}", "Sạc dự phòng {w}", "Cáp sạc {w}", "Cục sạc {w}"],
    "art-supplies":  ["Bút màu {w}", "Sơn acrylic {w}", "Bộ vẽ {w}", "Dụng cụ mỹ thuật {w}"],
    "desk-decor":    ["Đèn bàn {w}", "Kệ sách mini {w}", "Thảm chuột {w}", "Trang trí bàn {w}", "Bàn học {w}", "Ghế xoay {w}"],
    "souvenirs":     ["Móc khóa {w}", "Sticker {w}", "Túi vải {w}", "Thẻ treo {w}"],
    "snacks":        ["Bánh snack {w}", "Kẹo dẻo {w}", "Sô cô la {w}", "Hạt dinh dưỡng {w}"],
    "personal-care": ["Máy cạo râu {w}", "Kem chống nắng {w}", "Sữa rửa mặt {w}", "Son dưỡng {w}"],
}

_WORDS = [
    "Galaxy", "Classic", "Smart", "Cool", "Retro", "Mini", "Pro",
    "Light", "Happy", "Lucky", "Magic", "Fresh", "Zen", "Eco",
    "Urban", "Color", "Dream", "Spark", "Fun", "Active",
]

_DESCRIPTIONS = {
    "books":         "phù hợp cho học sinh, sinh viên muốn phát triển kỹ năng và mở rộng kiến thức.",
    "stationery":    "chất lượng cao, tiện dụng cho việc ghi chép hằng ngày và học tập.",
    "toys":          "giúp trẻ phát triển tư duy sáng tạo và kỹ năng vận động.",
    "gift-packs":    "được đóng gói đẹp mắt, phù hợp làm quà tặng dịp sinh nhật và tựu trường.",
    "backpacks":     "thiết kế chống thấm, nhẹ, nhiều ngăn tiện lợi cho học sinh và sinh viên.",
    "water-bottles": "giữ nhiệt tốt, an toàn vệ sinh, phù hợp mang theo khi đi học và hoạt động.",
    "study-tech":    "hỗ trợ học tập hiệu quả với thiết kế nhỏ gọn và dễ sử dụng.",
    "art-supplies":  "màu sắc tươi sáng, chất lượng bền, dành cho học sinh yêu thích mỹ thuật.",
    "desk-decor":    "giúp góc học tập gọn gàng, truyền cảm hứng và thể hiện cá tính.",
    "souvenirs":     "dễ thương, nhỏ gọn, phù hợp làm quà tặng hoặc sưu tầm.",
    "snacks":        "ngon miệng, cung cấp năng lượng nhanh chóng cho giờ giải lao.",
    "personal-care": "chất lượng an toàn, giúp bạn luôn tự tin và chỉn chu.",
}


def _generate_bulk_products() -> list[dict]:
    """
    Sinh danh sách sản phẩm fallback phủ đầy đủ 10 danh mục.
    Kết hợp mỗi template × một tập từ khóa → ~80 sản phẩm, cố định, không random.
    """
    products = []
    uid = 1
    for slug, meta in _CATEGORY_META.items():
        templates = _TEMPLATES[slug]
        lo, hi, step = meta["prices"]
        price_levels = list(range(lo, hi + 1, step))
        desc_suffix = _DESCRIPTIONS[slug]

        for t_idx, template in enumerate(templates):
            # Lấy 2 từ cho mỗi template để không bị quá nhiều sản phẩm trùng tên
            words_for_template = _WORDS[t_idx * 5: t_idx * 5 + 5]
            for w_idx, word in enumerate(words_for_template):
                name = template.format(w=word)
                price = price_levels[((t_idx * 5 + w_idx) % len(price_levels))]
                stock = 30 + (uid % 8) * 20  # 30~170, cố định
                sku = f"{slug[:3].upper()}-{word.upper()}-{uid:03d}"
                products.append({
                    "name": name,
                    "sku": sku,
                    "price": price,
                    "stock_quantity": stock,
                    "category_slug": slug,
                    "category_name": meta["name"],
                    "product_type_slug": meta["type"],
                    "description": f"{name} {desc_suffix}",
                    "attributes": {},
                })
                uid += 1
    return products


# ─────────────────────────────────────────────────────────────
# Sản phẩm curated (gốc) + bulk generated
# ─────────────────────────────────────────────────────────────
_CURATED_PRODUCTS = [
    {
        "name": "Atomic Habits",
        "sku": "BOOK-ATOMIC-HABITS",
        "price": 119000,
        "stock_quantity": 150,
        "category_slug": "books",
        "category_name": "Sách",
        "product_type_slug": "book",
        "description": "Sách self-help tiếng Anh về xây dựng thói quen bền vững.",
        "attributes": {"language": "en", "genre": "Self-Help", "author": "James Clear"},
    },
    {
        "name": "Sổ tay Campus B5",
        "sku": "STA-CAMPUS-B5",
        "price": 45000,
        "stock_quantity": 300,
        "category_slug": "stationery",
        "category_name": "Dụng cụ học tập",
        "product_type_slug": "stationery",
        "description": "Sổ tay giấy mịn phù hợp ghi chép hằng ngày và học nhóm.",
        "attributes": {"size": "B5", "pages": 120},
    },
    {
        "name": "Lego Creative Box",
        "sku": "TOY-LEGO-CREATIVE",
        "price": 399000,
        "stock_quantity": 80,
        "category_slug": "toys",
        "category_name": "Đồ chơi",
        "product_type_slug": "toy",
        "description": "Bộ LEGO sáng tạo giúp trẻ phát triển tư duy và phối màu.",
        "attributes": {"age_group": "6+", "pieces": 250},
    },
    {
        "name": "Gói quà Back To School",
        "sku": "GIFT-BTS-01",
        "price": 199000,
        "stock_quantity": 120,
        "category_slug": "gift-packs",
        "category_name": "Gói quà",
        "product_type_slug": "gift-pack",
        "description": "Combo quà tặng gồm sổ, bút, sticker cho mùa tựu trường.",
        "attributes": {"occasion": "back_to_school", "items": 5},
    },
    {
        "name": "Ba lô Miti Active",
        "sku": "BAG-MITI-ACTIVE",
        "price": 349000,
        "stock_quantity": 95,
        "category_slug": "backpacks",
        "category_name": "Ba lô",
        "product_type_slug": "backpack",
        "description": "Ba lô chống thấm nhẹ với nhiều ngăn cho học sinh, sinh viên.",
        "attributes": {"capacity": "20L", "color": "navy"},
    },
    {
        "name": "Bình giữ nhiệt LocknLock 500ml",
        "sku": "BOT-LOCK-500",
        "price": 229000,
        "stock_quantity": 140,
        "category_slug": "water-bottles",
        "category_name": "Bình nước",
        "product_type_slug": "bottle",
        "description": "Bình inox giữ nhiệt phù hợp mang theo khi đi học hoặc đi làm.",
        "attributes": {"volume": "500ml", "material": "stainless_steel"},
    },
    {
        "name": "Máy tính Casio FX-580VN X",
        "sku": "TECH-CASIO-580VNX",
        "price": 715000,
        "stock_quantity": 60,
        "category_slug": "study-tech",
        "category_name": "Đồ điện tử học tập",
        "product_type_slug": "study-tech",
        "description": "Máy tính khoa học dành cho học sinh THPT và sinh viên khối kỹ thuật.",
        "attributes": {"battery": "AAA", "exam_support": "high_school"},
    },
    {
        "name": "Đồng hồ Learny Watch",
        "sku": "TECH-LEARNY-WATCH",
        "price": 350000,
        "stock_quantity": 90,
        "category_slug": "study-tech",
        "category_name": "Đồ điện tử học tập",
        "product_type_slug": "study-tech",
        "description": "Đồng hồ thông minh nhỏ gọn giúp xem giờ và nhắc lịch học tập.",
        "attributes": {"display": "LED", "battery": "Li-ion", "features": "xem gio, nhac lich"},
    },
    {
        "name": "Bộ chì màu Faber-Castell 24 màu",
        "sku": "ART-FABER-24",
        "price": 189000,
        "stock_quantity": 110,
        "category_slug": "art-supplies",
        "category_name": "Mỹ thuật",
        "product_type_slug": "art-supply",
        "description": "Bộ chì màu chất lượng cao dành cho học sinh yêu thích mỹ thuật.",
        "attributes": {"colors": 24, "target": "students"},
    },
    {
        "name": "Đèn bàn Minihome Focus",
        "sku": "DECOR-MINI-LAMP",
        "price": 259000,
        "stock_quantity": 70,
        "category_slug": "desk-decor",
        "category_name": "Đồ trang trí bàn học",
        "product_type_slug": "desk-decor",
        "description": "Đèn bàn LED với ba chế độ sáng cho góc học tập hiện đại.",
        "attributes": {"light_mode": 3, "power": "USB"},
    },
    {
        "name": "Móc khóa Moji Capybara",
        "sku": "SOU-MOJI-CAPY",
        "price": 59000,
        "stock_quantity": 180,
        "category_slug": "souvenirs",
        "category_name": "Đồ lưu niệm",
        "product_type_slug": "souvenir",
        "description": "Móc khóa plush dễ thương dùng làm quà tặng hoặc phụ kiện balo.",
        "attributes": {"theme": "capybara", "material": "plush"},
    },
    {
        "name": "Máy cạo râu Xiaomi",
        "sku": "CARE-XIAOMI-01",
        "price": 250000,
        "stock_quantity": 50,
        "category_slug": "personal-care",
        "category_name": "Chăm sóc cá nhân",
        "product_type_slug": "personal-care",
        "description": "Máy cạo râu điện mini, pin sạc siêu khỏe, phù hợp mang đi du lịch.",
        "attributes": {"brand": "Xiaomi", "battery": "Type-C"},
    },
    {
        "name": "Sạc dự phòng Anker 10000mAh",
        "sku": "TECH-ANKER-10K",
        "price": 450000,
        "stock_quantity": 120,
        "category_slug": "study-tech",
        "category_name": "Đồ điện tử học tập",
        "product_type_slug": "study-tech",
        "description": "Pin sạc dự phòng dung lượng lớn, sạc nhanh an toàn cho điện thoại.",
        "attributes": {"capacity": "10000mAh", "brand": "Anker"},
    },
    {
        "name": "Snack khoai tây Lay's",
        "sku": "SNACK-LAYS-01",
        "price": 15000,
        "stock_quantity": 300,
        "category_slug": "snacks",
        "category_name": "Đồ ăn vặt",
        "product_type_slug": "snack",
        "description": "Snack khoai tây chiên giòn rụm, nhiều vị thơm ngon.",
        "attributes": {"flavor": "Truyền thống", "weight": "60g"},
    },
]

DEFAULT_PRODUCTS = _CURATED_PRODUCTS + _generate_bulk_products()
