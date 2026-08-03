import re
from dataclasses import dataclass

TIER_PAYMENT = 3
TIER_TOTAL = 2
TIER_CURRENCY = 1


@dataclass(frozen=True)
class AnchorMatch:
    start: int
    end: int
    tier: int
    label: str


PAYMENT_PATTERNS = (
    (r"всего\s+к\s+оплате", "всего к оплате"),
    (r"сумма\s+к\s+оплате", "сумма к оплате"),
    (r"итог\s*к?\s*оплате", "итог к оплате"),
    (r"к\s+оплате", "к оплате"),
    (r"до\s+сплати", "до сплати"),
    (r"разом\s+по\s+чеку", "разом по чеку"),
    (r"amount\s+due", "amount due"),
    (r"balance\s+due", "balance due"),
    (r"grand\s+total", "grand total"),
    (r"оплата\s+товару", "оплата товару"),
)

TOTAL_PATTERNS = (
    (r"п[іиі]дсумок|подсумок", "підсумок"),
    (r"итого|itogo", "итого"),
    (r"итог", "итог"),
    (r"сумма", "сумма"),
    (r"\bсума\b|\bсуны\b|\bсуна\b|\bсука\b|\bсуни\b", "сума"),
    (r"всього", "всього"),
    (r"всего", "всего"),
    (r"разом", "разом"),
    (r"\btotal\b", "total"),
    (r"\bamount\b", "amount"),
)

CURRENCY_PATTERNS = (
    (r"г\s*р\s*н|гривн|\bгри\b", "грн"),
    (r"руб(?:л|$|\s)|₽", "руб"),
    (r"[$€₴]", "currency_symbol"),
    (r"\buah\b|\busd\b|\beur\b", "currency_code"),
)


def normalize_keyword_line(line: str) -> str:
    lowered = line.lower().replace("ё", "е")
    lowered = lowered.replace("ґ", "г")
    return re.sub(r"[^\w\s$€₴₽]", " ", lowered, flags=re.UNICODE)


def find_anchors(line: str) -> list[AnchorMatch]:
    normalized = normalize_keyword_line(line)
    matches: list[AnchorMatch] = []

    for pattern, label in PAYMENT_PATTERNS:
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            matches.append(
                AnchorMatch(match.start(), match.end(), TIER_PAYMENT, label)
            )

    for pattern, label in TOTAL_PATTERNS:
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            matches.append(AnchorMatch(match.start(), match.end(), TIER_TOTAL, label))

    for pattern, label in CURRENCY_PATTERNS:
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            matches.append(
                AnchorMatch(match.start(), match.end(), TIER_CURRENCY, label)
            )

    return _dedupe_anchors(matches)


def _dedupe_anchors(matches: list[AnchorMatch]) -> list[AnchorMatch]:
    if not matches:
        return []
    ordered = sorted(matches, key=lambda item: (item.start, -item.tier, -(item.end - item.start)))
    kept: list[AnchorMatch] = []
    for item in ordered:
        overlaps = False
        for existing in kept:
            if item.start < existing.end and item.end > existing.start:
                overlaps = True
                break
        if not overlaps:
            kept.append(item)
    return kept


def looks_like_date_line(line: str) -> bool:
    return bool(re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", line))
