STRONG_AMOUNT_SOURCES = frozenset(
    {
        "payment",
        "keyword",
        "всего",
        "всього",
        "итого",
        "итог",
        "сума",
        "сумма",
        "reconciled_change",
        "consensus",
        "к оплате",
        "до сплати",
        "разом по чеку",
        "грн",
    }
)


def _prefer_regex_amount(llm_result: dict, regex_result: dict) -> bool:
    if not regex_result.get("amount_confident"):
        return False
    if not llm_result.get("amount_confident"):
        return True
    if llm_result.get("amount") == regex_result.get("amount"):
        return False
    source = regex_result.get("amount_matched_by") or ""
    if source in STRONG_AMOUNT_SOURCES or source.startswith("reconcil"):
        return True
    if llm_result.get("llm_confidence") == "low":
        return True
    return False


def _prefer_regex_date(llm_result: dict, regex_result: dict) -> bool:
    if not regex_result.get("date_confident"):
        return False
    if not llm_result.get("date_confident"):
        return True
    if llm_result.get("purchase_date") == regex_result.get("purchase_date"):
        return False
    matched = regex_result.get("date_matched_by") or ""
    return "time" in matched or matched.startswith("operation")


def _prefer_regex_merchant(llm_result: dict, regex_result: dict) -> bool:
    if not regex_result.get("merchant_confident"):
        return False
    if not llm_result.get("merchant_confident"):
        return True
    if regex_result.get("merchant_matched_by") == "known":
        llm_name = (llm_result.get("merchant_name") or "").lower()
        regex_name = (regex_result.get("merchant_name") or "").lower()
        if regex_name and regex_name not in llm_name and llm_name not in regex_name:
            return True
    return False


def merge_hybrid_results(llm_result: dict, regex_result: dict) -> dict:
    merged = dict(llm_result)
    merged["parser_mode"] = "hybrid"
    filled_from_regex: list[str] = []

    if _prefer_regex_amount(llm_result, regex_result):
        merged["amount"] = regex_result["amount"]
        merged["amount_matched_by"] = regex_result["amount_matched_by"]
        merged["amount_source"] = regex_result["amount_source"]
        merged["amount_confident"] = True
        filled_from_regex.append("amount")

    if _prefer_regex_date(llm_result, regex_result):
        merged["purchase_date"] = regex_result["purchase_date"]
        merged["date_matched_by"] = regex_result["date_matched_by"]
        merged["date_source"] = regex_result["date_source"]
        merged["date_confident"] = True
        filled_from_regex.append("date")

    if _prefer_regex_merchant(llm_result, regex_result):
        merged["merchant_name"] = regex_result["merchant_name"]
        merged["merchant_matched_by"] = regex_result["merchant_matched_by"]
        merged["merchant_source"] = regex_result["merchant_source"]
        merged["merchant_confident"] = True
        filled_from_regex.append("merchant")

    regex_currency = regex_result.get("currency")
    llm_currency = llm_result.get("currency")
    if regex_currency and regex_currency != llm_currency:
        merged["currency"] = regex_currency
        filled_from_regex.append("currency")
    elif not merged.get("currency") and regex_currency:
        merged["currency"] = regex_currency
        filled_from_regex.append("currency")

    regex_category = regex_result.get("category")
    llm_category = llm_result.get("category")
    if regex_category and regex_category != llm_category:
        merged["category"] = regex_category
        filled_from_regex.append("category")
    elif not merged.get("category") and regex_category:
        merged["category"] = regex_category
        filled_from_regex.append("category")

    merged["all_key_fields_missing"] = not (
        merged.get("amount_confident")
        or merged.get("date_confident")
        or merged.get("merchant_confident")
    )
    merged["needs_manual_review"] = bool(
        merged["all_key_fields_missing"]
        or (
            llm_result.get("needs_manual_review")
            and not (
                merged.get("amount_confident")
                and merged.get("date_confident")
                and merged.get("merchant_confident")
            )
        )
        or regex_result.get("amount_matched_by") == "ambiguous"
    )
    if filled_from_regex:
        merged["hybrid_filled_from_regex"] = filled_from_regex
    return merged
