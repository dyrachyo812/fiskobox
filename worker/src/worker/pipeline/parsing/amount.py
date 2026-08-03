import re
from dataclasses import dataclass
from decimal import Decimal

from worker.pipeline.parsing.amountAnchors import (
    TIER_CURRENCY,
    TIER_PAYMENT,
    TIER_TOTAL,
    find_anchors,
    looks_like_date_line,
    normalize_keyword_line,
)
from worker.pipeline.parsing.amountExclusions import (
    is_excluded_amount_token,
    is_multiply_line,
    is_non_money_line,
)
from worker.pipeline.parsing.amountNormalize import (
    find_amount_tokens,
    normalize,
    normalize_amount,
)
from worker.pipeline.parsing.amountTender import (
    extract_multiply_products,
    extract_tender_and_change,
    is_tender_or_change_line,
    reconcile_total_with_change,
)

SOURCE_BY_TIER = {
    TIER_PAYMENT: "payment",
    TIER_TOTAL: "keyword",
    TIER_CURRENCY: "currency",
}


@dataclass(frozen=True)
class AmountCandidate:
    value: Decimal
    line_index: int
    token_start: int
    tier: int
    has_decimal: bool
    anchor_label: str


def _token_has_decimal(token: str) -> bool:
    return "." in token or "," in token


def _next_nonempty_line(lines: list[str], index: int) -> str | None:
    for line in lines[index + 1 : index + 4]:
        if line.strip():
            return line
    return None


def _prev_nonempty_line(lines: list[str], index: int) -> str | None:
    start = max(0, index - 3)
    for line in reversed(lines[start:index]):
        if line.strip():
            return line
    return None


def _values_from_line(
    line: str,
    *,
    allow_plain_integer: bool,
    prefer_after: int | None = None,
) -> list[tuple[Decimal, int, bool]]:
    values: list[tuple[Decimal, int, bool]] = []
    for token, start in find_amount_tokens(line):
        if is_excluded_amount_token(token, line):
            continue
        if prefer_after is not None and start + len(token) <= prefer_after:
            continue
        value = normalize_amount(token, allow_plain_integer=allow_plain_integer)
        if value is None:
            continue
        values.append((value, start, _token_has_decimal(token)))
    return values


def _collect_candidates(text: str) -> list[AmountCandidate]:
    lines = text.splitlines()
    candidates: list[AmountCandidate] = []

    for index, line in enumerate(lines):
        if not line.strip() or is_multiply_line(line):
            continue
        if is_tender_or_change_line(line):
            continue
        if is_non_money_line(line) and not find_anchors(line):
            continue

        anchors = find_anchors(line)
        if not anchors:
            continue

        next_line = _next_nonempty_line(lines, index)
        prev_line = _prev_nonempty_line(lines, index)
        if next_line and is_tender_or_change_line(next_line):
            next_line = None

        for anchor in anchors:
            allow_plain = True
            same_line = _values_from_line(
                line,
                allow_plain_integer=allow_plain,
                prefer_after=anchor.start,
            )
            if not same_line:
                same_line = _values_from_line(line, allow_plain_integer=allow_plain)

            chosen = same_line
            if not chosen and next_line and not looks_like_date_line(next_line):
                if not is_multiply_line(next_line) and not is_non_money_line(next_line):
                    chosen = _values_from_line(
                        next_line,
                        allow_plain_integer=allow_plain,
                    )
            if (
                not chosen
                and prev_line
                and anchor.tier == TIER_CURRENCY
                and not looks_like_date_line(prev_line)
                and not is_multiply_line(prev_line)
            ):
                chosen = _values_from_line(
                    prev_line,
                    allow_plain_integer=True,
                )

            if anchor.tier == TIER_CURRENCY:
                decimal_only = [item for item in chosen if item[2]]
                if decimal_only:
                    chosen = decimal_only
                else:
                    chosen = [
                        item
                        for item in chosen
                        if item[0] < Decimal(100000)
                        and item[0] == item[0].to_integral_value()
                    ]

            if not chosen:
                continue

            if len(chosen) > 1 and same_line:
                after_anchor = [item for item in chosen if item[1] >= anchor.end]
                if after_anchor:
                    chosen = [min(after_anchor, key=lambda item: item[1])]
                else:
                    chosen = [min(chosen, key=lambda item: abs(item[1] - anchor.end))]
            elif len(chosen) > 1:
                chosen = [chosen[0]]

            value, token_start, has_decimal = chosen[0]
            candidates.append(
                AmountCandidate(
                    value=value,
                    line_index=index,
                    token_start=token_start,
                    tier=anchor.tier,
                    has_decimal=has_decimal,
                    anchor_label=anchor.label,
                )
            )

    return candidates


def _pick_label(pool: list[AmountCandidate], value: Decimal) -> str:
    matches = [item for item in pool if item.value == value]
    if not matches:
        return SOURCE_BY_TIER[pool[0].tier]
    last = max(matches, key=lambda item: (item.line_index, item.token_start))
    return last.anchor_label


def _resolve_candidates(
    candidates: list[AmountCandidate],
    *,
    raw_text: str,
) -> tuple[Decimal | None, str]:
    if not candidates:
        return None, "none"

    tender, change = extract_tender_and_change(raw_text)
    products = extract_multiply_products(raw_text)
    reconciled = reconcile_total_with_change(
        [item.value for item in candidates],
        tender=tender,
        change=change,
        products=products,
    )
    if reconciled is not None:
        return reconciled, "reconciled_change"

    vsego_pool = [
        item
        for item in candidates
        if item.anchor_label in {"всего", "всього", "grand total"}
    ]
    if vsego_pool:
        unique_vsego = {item.value for item in vsego_pool}
        if len(unique_vsego) == 1:
            value = next(iter(unique_vsego))
            return value, _pick_label(vsego_pool, value)

    best_tier = max(item.tier for item in candidates)
    pool = [item for item in candidates if item.tier == best_tier]

    unique_all = {item.value for item in pool}
    if len(unique_all) == 1:
        value = next(iter(unique_all))
        return value, _pick_label(pool, value)

    counts: dict[Decimal, int] = {}
    for item in pool:
        counts[item.value] = counts.get(item.value, 0) + 1
    top_count = max(counts.values())
    leaders = [value for value, count in counts.items() if count == top_count]
    if len(leaders) == 1 and top_count >= 2:
        value = leaders[0]
        return value, "consensus"

    all_counts: dict[Decimal, int] = {}
    for item in candidates:
        all_counts[item.value] = all_counts.get(item.value, 0) + 1
    all_top = max(all_counts.values())
    all_leaders = [
        value for value, count in all_counts.items() if count == all_top
    ]
    if len(all_leaders) == 1 and all_top >= 2:
        value = all_leaders[0]
        return value, "consensus"

    last_line = max(item.line_index for item in pool)
    last_pool = [item for item in pool if item.line_index == last_line]
    unique_last = {item.value for item in last_pool}
    if len(unique_last) == 1:
        value = next(iter(unique_last))
        return value, _pick_label(last_pool, value)

    return None, "ambiguous"


def extract_amount_with_source(text: str) -> tuple[Decimal | None, str]:
    if not text or not text.strip():
        return None, "none"

    candidates = _collect_candidates(text)
    return _resolve_candidates(candidates, raw_text=text)


def extract_amount(text: str) -> Decimal | None:
    amount, _source = extract_amount_with_source(text)
    return amount


def merge_payment_evidence(texts: list[str]) -> str:
    snippets: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(
        r"(грн|до сплати|к оплате|amount due|сум[ама]|иог|итог|total|разом|всього)",
        re.IGNORECASE,
    )
    for text in texts:
        for line in text.splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned in seen:
                continue
            if pattern.search(cleaned) and find_amount_tokens(cleaned):
                seen.add(cleaned)
                snippets.append(cleaned)
    return "\n".join(snippets)


__all__ = [
    "extract_amount",
    "extract_amount_with_source",
    "merge_payment_evidence",
    "normalize",
    "normalize_keyword_line",
]
