import re

CURRENCY_LABELS = {
    "UAH": "грн",
    "RUB": "руб",
    "USD": "$",
    "EUR": "€",
}

EXPLICIT_PATTERNS: list[tuple[str, re.Pattern[str], int]] = [
    ("UAH", re.compile(r"\bг\s*р\s*н\b", re.IGNORECASE), 30),
    ("UAH", re.compile(r"грн", re.IGNORECASE), 28),
    ("UAH", re.compile(r"гривн", re.IGNORECASE), 28),
    ("UAH", re.compile(r"₴"), 28),
    ("UAH", re.compile(r"\buah\b", re.IGNORECASE), 28),
    ("UAH", re.compile(r"\bgrn\b", re.IGNORECASE), 16),
    ("RUB", re.compile(r"\bруб(?:л|\b|\.)", re.IGNORECASE), 28),
    ("RUB", re.compile(r"₽"), 28),
    ("RUB", re.compile(r"\brub\b", re.IGNORECASE), 28),
    ("RUB", re.compile(r"(?<!\w)р\.(?=\s|$)"), 12),
    ("USD", re.compile(r"\busd\b", re.IGNORECASE), 28),
    ("USD", re.compile(r"\$\s*\d{1,5}(?:[.,]\d{2})?|\d{1,5}(?:[.,]\d{2})?\s*\$"), 16),
    ("EUR", re.compile(r"\beur\b", re.IGNORECASE), 28),
    ("EUR", re.compile(r"€"), 28),
]

LOCALE_HINTS: list[tuple[str, re.Pattern[str], int]] = [
    ("UAH", re.compile(r"\bсума\b", re.IGNORECASE), 6),
    ("UAH", re.compile(r"\bкартка\b", re.IGNORECASE), 6),
    ("UAH", re.compile(r"\bфіскальн", re.IGNORECASE), 6),
    ("UAH", re.compile(r"\bдо сплати\b", re.IGNORECASE), 6),
    ("UAH", re.compile(r"\bвсього\b", re.IGNORECASE), 5),
    ("UAH", re.compile(r"\bпдв\b", re.IGNORECASE), 6),
    ("UAH", re.compile(r"\bрешта\b", re.IGNORECASE), 8),
    ("UAH", re.compile(r"\bготівк", re.IGNORECASE), 6),
    ("UAH", re.compile(r"\bфоп\b", re.IGNORECASE), 3),
    ("UAH", re.compile(r"\bпіі\b", re.IGNORECASE), 3),
    ("UAH", re.compile(r"\bтов\b", re.IGNORECASE), 3),
    ("UAH", re.compile(r"\bкрим\b", re.IGNORECASE), 4),
    ("UAH", re.compile(r"\bм\.\s*\w+", re.IGNORECASE), 2),
    ("RUB", re.compile(r"\bитого\b", re.IGNORECASE), 2),
    ("RUB", re.compile(r"\bсумма\b", re.IGNORECASE), 2),
    ("RUB", re.compile(r"\bинн\b", re.IGNORECASE), 2),
]


def format_currency_label(code: str | None) -> str:
    if not code:
        return ""
    return CURRENCY_LABELS.get(code.upper(), code.upper())


def extract_currency(text: str | None) -> str | None:
    if not text or not text.strip():
        return None

    lowered = text.lower().replace("ё", "е")
    explicit_scores: dict[str, int] = {}
    hint_scores: dict[str, int] = {}

    for code, pattern, weight in EXPLICIT_PATTERNS:
        if pattern.search(lowered):
            explicit_scores[code] = explicit_scores.get(code, 0) + weight

    if explicit_scores:
        best_code = max(explicit_scores, key=explicit_scores.get)
        best_score = explicit_scores[best_code]
        rivals = [
            score for code, score in explicit_scores.items() if code != best_code
        ]
        if not rivals or best_score > max(rivals):
            return best_code

    for code, pattern, weight in LOCALE_HINTS:
        if pattern.search(lowered):
            hint_scores[code] = hint_scores.get(code, 0) + weight

    scores = {**hint_scores}
    for code, score in explicit_scores.items():
        scores[code] = scores.get(code, 0) + score

    if not scores:
        return None

    best_code = max(scores, key=scores.get)
    best_score = scores[best_code]
    rivals = [score for code, score in scores.items() if code != best_code]
    if rivals and best_score <= max(rivals):
        return None
    return best_code
