from shared.models import Category

RELIABLE_MERCHANT_SOURCES = frozenset({"known", "legal", "line"})

TEXT_CATEGORY_SIGNALS: dict[str, tuple[str, ...]] = {
    "Кафе": (
        "капучино",
        "капуччіно",
        "капуччино",
        "cappuccino",
        "еспресо",
        "espresso",
        "латте",
        "латте",
        "американо",
        "кава ",
        "кава\n",
        "кофе",
        "стейк",
        "steak",
        "салат",
        "салаt",
        "філе",
        "филе",
        "карпачо",
        "carpaccio",
        "рибай",
        "бургер",
        "піца",
        "пицца",
        "суши",
        "ресторан",
        "меню",
        "офіціант",
        "официант",
        "грейпфрут",
        "телятин",
        "яловичин",
    ),
    "Аптека": (
        "таблет",
        "капс.",
        "капс ",
        "ампул",
        "пор.д/",
        "pharmacy",
        "aptekar",
        "ліки",
        "лекарств",
    ),
    "Транспорт": (
        "бензин",
        "азс",
        "аі-95",
        "аи-95",
        "ai-95",
        "дизель",
        "пмм",
        "petrol",
    ),
    "Продукты": (
        "супермаркет",
        "гіпермаркет",
        "гипермаркет",
    ),
}


def _score_keywords(haystack: str, keywords: list[str] | tuple[str, ...]) -> int:
    hits = 0
    for keyword in keywords:
        if not keyword:
            continue
        token = keyword.lower()
        if token in haystack:
            hits += 1 + min(len(token.strip()), 12) // 4
    return hits


def _category_from_merchant(
    merchant_name: str,
    categories: list[Category],
) -> tuple[str | None, int]:
    haystack = merchant_name.lower().replace("ё", "е")
    best_name: str | None = None
    best_hits = 0
    for category in categories:
        hits = _score_keywords(haystack, category.keywords or [])
        if hits > best_hits:
            best_hits = hits
            best_name = category.name
    return best_name, best_hits


def _category_from_text(raw_text: str) -> tuple[str | None, int]:
    haystack = raw_text.lower().replace("ё", "е")
    best_name: str | None = None
    best_hits = 0
    for name, keywords in TEXT_CATEGORY_SIGNALS.items():
        hits = 0
        matched = 0
        for keyword in keywords:
            if keyword in haystack:
                matched += 1
                hits += 2 + min(len(keyword.strip()), 10) // 3
        if matched >= 2:
            hits += 4
        if hits > best_hits:
            best_hits = hits
            best_name = name
    if best_hits < 4:
        return None, 0
    return best_name, best_hits


def categorize(
    merchant_name: str | None,
    categories: list[Category],
    raw_text: str | None = None,
    *,
    merchant_source: str | None = None,
) -> str | None:
    if not categories:
        return None

    merchant_category = None
    merchant_hits = 0
    reliable = (
        merchant_source is None or merchant_source in RELIABLE_MERCHANT_SOURCES
    )
    if reliable and merchant_name and merchant_name.strip():
        merchant_category, merchant_hits = _category_from_merchant(
            merchant_name, categories
        )

    text_category = None
    text_hits = 0
    if raw_text and raw_text.strip():
        text_category, text_hits = _category_from_text(raw_text)

    if text_category and text_hits >= 8 and (
        merchant_category is None or text_hits > merchant_hits + 2
    ):
        return text_category

    if merchant_category is not None:
        return merchant_category

    if text_category is not None:
        return text_category

    return None
