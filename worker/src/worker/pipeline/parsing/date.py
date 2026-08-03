from dataclasses import dataclass
from datetime import date

from worker.pipeline.parsing.dateExclusions import (
    is_hint_line,
    is_non_date_line,
    is_operation_line,
    is_print_line,
)
from worker.pipeline.parsing.dateParse import (
    dates_on_line,
    dates_with_time_on_line,
    is_plausible,
    line_has_time,
    parse_text_date,
    parse_token,
)

TIER_TIMED_OPERATION = 4
TIER_TIMED = 3
TIER_OPERATION = 2
TIER_HINT = 1
TIER_PLAIN = 0
TIER_PRINT = -1

TIER_LABELS = {
    TIER_TIMED_OPERATION: "operation_with_time",
    TIER_TIMED: "with_time",
    TIER_OPERATION: "operation",
    TIER_HINT: "hint",
    TIER_PLAIN: "plain",
    TIER_PRINT: "print",
}


@dataclass(frozen=True)
class DateCandidate:
    value: date
    line_index: int
    tier: int
    pattern: str


def _nearby_has_time(lines: list[str], index: int) -> bool:
    if line_has_time(lines[index]):
        return True
    if index > 0 and line_has_time(lines[index - 1]):
        return True
    if index + 1 < len(lines) and line_has_time(lines[index + 1]):
        return True
    return False


def _collect_candidates(text: str, today: date | None = None) -> list[DateCandidate]:
    lines = text.splitlines()
    candidates: list[DateCandidate] = []

    for index, line in enumerate(lines):
        if not line.strip():
            continue

        print_line = is_print_line(line)
        operation_line = is_operation_line(line) and not print_line
        hint_line = is_hint_line(line) and not print_line
        non_date = is_non_date_line(line)

        same_line_timed = dates_with_time_on_line(line, today)
        for parsed in same_line_timed:
            tier = TIER_TIMED_OPERATION if operation_line else TIER_TIMED
            pattern = "date_with_time"
            if operation_line:
                pattern = "operation_date_with_time"
            candidates.append(DateCandidate(parsed, index, tier, pattern))

        if non_date and not same_line_timed:
            continue

        for parsed in dates_on_line(line, today):
            if parsed in same_line_timed:
                continue

            near_time = _nearby_has_time(lines, index)
            if print_line:
                tier = TIER_PRINT
                pattern = "print_date"
            elif near_time and operation_line:
                tier = TIER_TIMED_OPERATION
                pattern = "operation_date_near_time"
            elif near_time:
                tier = TIER_TIMED
                pattern = "date_near_time"
            elif operation_line:
                tier = TIER_OPERATION
                pattern = "operation_date"
            elif hint_line:
                tier = TIER_HINT
                pattern = "hint_date"
            else:
                tier = TIER_PLAIN
                pattern = "plain_date"
            candidates.append(DateCandidate(parsed, index, tier, pattern))

    return candidates


def _resolve_candidates(
    candidates: list[DateCandidate],
) -> tuple[date | None, str]:
    if not candidates:
        return None, "none"

    best_tier = max(item.tier for item in candidates)
    pool = [item for item in candidates if item.tier == best_tier]
    pool.sort(key=lambda item: item.line_index)
    winner = pool[0]
    return winner.value, winner.pattern


def extract_date_with_source(
    text: str, today: date | None = None
) -> tuple[date | None, str]:
    if not text or not text.strip():
        return None, "none"
    candidates = _collect_candidates(text, today)
    return _resolve_candidates(candidates)


def extract_date(text: str, today: date | None = None) -> date | None:
    value, _source = extract_date_with_source(text, today)
    return value


__all__ = [
    "extract_date",
    "extract_date_with_source",
    "is_plausible",
    "parse_text_date",
    "parse_token",
]
