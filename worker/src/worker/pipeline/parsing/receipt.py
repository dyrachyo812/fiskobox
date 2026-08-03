from shared.config import get_settings
from shared.logging import get_logger
from shared.models import Category

from worker.pipeline.parsing.amount import extract_amount_with_source
from worker.pipeline.parsing.categorize import categorize
from worker.pipeline.parsing.currency import extract_currency
from worker.pipeline.parsing.date import extract_date_with_source
from worker.pipeline.parsing.hybridMerge import merge_hybrid_results
from worker.pipeline.parsing.merchant import extract_merchant_with_source
from worker.pipeline.parsing.ollamaClient import OllamaClient
from worker.pipeline.parsing.ollamaParser import OllamaReceiptParser

logger = get_logger(__name__)

RELIABLE_MERCHANT = frozenset({"known", "legal", "line"})


def parse_receipt_regex(raw_text: str, categories: list[Category]) -> dict:
    merchant_name, merchant_source = extract_merchant_with_source(raw_text)
    amount, amount_matched_by = extract_amount_with_source(raw_text)
    purchase_date, date_matched_by = extract_date_with_source(raw_text)

    amount_confident = amount is not None and amount_matched_by not in {
        "none",
        "ambiguous",
    }
    date_confident = purchase_date is not None and date_matched_by != "none"
    merchant_confident = (
        merchant_name is not None and merchant_source in RELIABLE_MERCHANT
    )

    all_key_fields_missing = (
        not amount_confident and not date_confident and not merchant_confident
    )
    needs_manual_review = (
        amount_matched_by == "ambiguous"
        or merchant_source == "rejected"
        or all_key_fields_missing
    )

    return {
        "amount": amount,
        "currency": extract_currency(raw_text),
        "merchant_name": merchant_name,
        "purchase_date": purchase_date,
        "category": categorize(
            merchant_name,
            categories,
            raw_text,
            merchant_source=merchant_source,
        ),
        "items": [],
        "needs_manual_review": needs_manual_review,
        "all_key_fields_missing": all_key_fields_missing,
        "amount_matched_by": amount_matched_by,
        "date_matched_by": date_matched_by,
        "merchant_matched_by": merchant_source,
        "amount_source": amount_matched_by,
        "merchant_source": merchant_source,
        "date_source": date_matched_by,
        "amount_confident": amount_confident,
        "date_confident": date_confident,
        "merchant_confident": merchant_confident,
        "parser_mode": "regex",
    }


def build_ollama_parser() -> OllamaReceiptParser:
    settings = get_settings()
    client = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
        temperature=settings.ollama_temperature,
    )
    return OllamaReceiptParser(client)


def parse_receipt_llm(raw_text: str, categories: list[Category]) -> dict:
    return build_ollama_parser().parse(raw_text, categories)


def parse_receipt_hybrid(raw_text: str, categories: list[Category]) -> dict:
    llm_result = parse_receipt_llm(raw_text, categories)
    regex_result = parse_receipt_regex(raw_text, categories)

    if llm_result.get("parser_error"):
        logger.warning(
            "Hybrid parser: Ollama failed, using regex",
            extra={"parser_error": llm_result.get("parser_error")},
        )
        regex_result["parser_mode"] = "hybrid"
        regex_result["llm_fallback_reason"] = llm_result.get("parser_error")
        if regex_result.get("all_key_fields_missing"):
            regex_result["needs_manual_review"] = True
        return regex_result

    merged = merge_hybrid_results(llm_result, regex_result)
    if merged.get("all_key_fields_missing"):
        merged["needs_manual_review"] = True
    return merged


def parse_receipt(
    raw_text: str,
    categories: list[Category],
    *,
    mode: str | None = None,
) -> dict:
    settings = get_settings()
    selected = (mode or settings.parser_mode or "regex").strip().lower()

    if selected == "regex":
        return parse_receipt_regex(raw_text, categories)
    if selected == "llm":
        return parse_receipt_llm(raw_text, categories)
    if selected == "hybrid":
        return parse_receipt_hybrid(raw_text, categories)

    raise ValueError(
        f"Unsupported PARSER_MODE: {selected}. Use llm|regex|hybrid."
    )
