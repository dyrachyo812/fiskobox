from worker.pipeline.parsing.merchantFilters import (
    MAX_LENGTH,
    clean_merchant,
    is_plausible_merchant_name,
    is_service_only,
    is_skipped_line,
    looks_like_ocr_garbage,
)
from worker.pipeline.parsing.merchantKnown import find_known_merchant
from worker.pipeline.parsing.merchantLegal import extract_legal_merchant

SCAN_LINES = 30
FALLBACK_LINES = 12


def extract_merchant_with_source(text: str) -> tuple[str | None, str]:
    if not text or not text.strip():
        return None, "none"

    known = find_known_merchant(text)
    if known is not None:
        return known, "known"

    lines = text.splitlines()[:SCAN_LINES]
    rejected = False

    for line in lines:
        stripped = line.strip()
        if looks_like_ocr_garbage(stripped) and sum(
            character.isalpha() for character in stripped
        ) >= 3:
            rejected = True
        legal = extract_legal_merchant(line)
        if legal is None:
            continue
        cleaned = clean_merchant(legal)
        if cleaned is None or not is_plausible_merchant_name(cleaned):
            rejected = True
            continue
        return cleaned, "legal"

    for line in lines[:FALLBACK_LINES]:
        candidate = line.strip()
        if is_skipped_line(candidate):
            continue
        cleaned = clean_merchant(candidate)
        if cleaned is None:
            if candidate and not is_service_only(candidate):
                rejected = True
            continue
        if not is_plausible_merchant_name(cleaned):
            rejected = True
            continue
        return cleaned[:MAX_LENGTH], "line"

    if rejected:
        return None, "rejected"
    return None, "none"


def extract_merchant(text: str) -> str | None:
    merchant, _source = extract_merchant_with_source(text)
    return merchant


__all__ = ["extract_merchant", "extract_merchant_with_source"]
