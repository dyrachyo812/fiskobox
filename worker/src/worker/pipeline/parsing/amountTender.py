import re
from decimal import Decimal

from worker.pipeline.parsing.amountNormalize import find_amount_tokens, normalize_amount

TENDER_LINE = re.compile(
    r"(?:"
    r"наличн(?:ыми|ые|ых)?|"
    r"готівки|отівки|отивки|"
    r"получено|внесено|"
    r"cash\s*(?:tendered|paid)?|paid\s*cash"
    r")",
    re.IGNORECASE,
)

CASH_GIVEN_LINE = re.compile(
    r"(?:"
    r"^\s*готівка\s*[:：]|"
    r"^\s*наличные\s*[:：]|"
    r"готівка\s*[:：]\s*[\d\s.,]+|"
    r"наличные\s*[:：]\s*[\d\s.,]+"
    r")",
    re.IGNORECASE,
)

PAYMENT_FORM_LINE = re.compile(r"форма\s*оплат", re.IGNORECASE)

CHANGE_LINE = re.compile(
    r"(?:"
    r"сдача|решта|сдaча|"
    r"\bchange\b"
    r")",
    re.IGNORECASE,
)

TOTALISH_LINE = re.compile(
    r"(?:"
    r"всего|всього|итого|итог|сумма|сума|разом|total|к\s*оплат|до\s*сплати"
    r")",
    re.IGNORECASE,
)

MULTIPLY_PAIR = re.compile(
    r"(?<!\d)(\d{1,5}[.,]\d{1,3})\s*[xх×X]\s*(\d{1,5}[.,]\d{1,3})(?!\d)",
)


def is_tender_or_change_line(line: str) -> bool:
    lowered = line.lower()
    if CHANGE_LINE.search(lowered):
        return True
    if PAYMENT_FORM_LINE.search(lowered):
        return False
    if TENDER_LINE.search(lowered) and not TOTALISH_LINE.search(lowered):
        return True
    if CASH_GIVEN_LINE.search(line) and not TOTALISH_LINE.search(lowered):
        return True
    return False


def _first_amount(line: str) -> Decimal | None:
    for token, _start in find_amount_tokens(line):
        value = normalize_amount(token, allow_plain_integer=True)
        if value is not None:
            return value
    return None


def extract_tender_and_change(text: str) -> tuple[Decimal | None, Decimal | None]:
    tender: Decimal | None = None
    change: Decimal | None = None
    tender_candidates: list[Decimal] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if change is None and CHANGE_LINE.search(lowered):
            change = _first_amount(stripped)
        if PAYMENT_FORM_LINE.search(lowered):
            continue
        if TENDER_LINE.search(lowered) or CASH_GIVEN_LINE.search(stripped):
            value = _first_amount(stripped)
            if value is not None:
                tender_candidates.append(value)

    if tender_candidates:
        if change is not None:
            tender = max(tender_candidates)
        else:
            tender = tender_candidates[0]
    return tender, change


def is_round_cash(value: Decimal) -> bool:
    return value >= Decimal(100) and value == value.to_integral_value()


def extract_multiply_products(text: str) -> list[Decimal]:
    products: list[Decimal] = []
    for left, right in MULTIPLY_PAIR.findall(text):
        a = normalize_amount(left, allow_plain_integer=False)
        b = normalize_amount(right, allow_plain_integer=False)
        if a is None or b is None:
            continue
        products.append((a * b).quantize(Decimal("0.01")))
    return products


def closest_candidate(
    candidates: list[Decimal],
    target: Decimal,
    *,
    max_delta: Decimal,
) -> Decimal | None:
    if not candidates:
        return None
    best = min(candidates, key=lambda value: abs(value - target))
    if abs(best - target) <= max_delta:
        return best
    return None


def reconcile_total_with_change(
    candidates: list[Decimal],
    *,
    tender: Decimal | None,
    change: Decimal | None,
    products: list[Decimal] | None = None,
) -> Decimal | None:
    unique = list(dict.fromkeys(candidates))
    if not unique:
        return None

    if products:
        for product in products:
            match = closest_candidate(unique, product, max_delta=Decimal("0.02"))
            if match is not None:
                return match

    if tender is not None and change is not None:
        expected = (tender - change).quantize(Decimal("0.01"))
        if expected > 0:
            exact = closest_candidate(unique, expected, max_delta=Decimal("0.01"))
            if exact is not None:
                return exact
            soft = closest_candidate(unique, expected, max_delta=Decimal("0.50"))
            if soft is not None:
                return soft

    if change is None or change <= 0:
        return None

    reconciled: list[Decimal] = []
    for value in unique:
        cash = (value + change).quantize(Decimal("0.01"))
        if is_round_cash(cash):
            reconciled.append(value)

    if not reconciled:
        return None
    if len(set(reconciled)) == 1:
        return reconciled[0]

    counts = {value: candidates.count(value) for value in set(reconciled)}
    top = max(counts.values())
    leaders = [value for value, count in counts.items() if count == top]
    if len(leaders) == 1:
        return leaders[0]
    return min(leaders)
