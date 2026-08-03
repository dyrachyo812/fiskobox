from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from worker.pipeline.parsing.ollamaPrompt import ALLOWED_CATEGORIES

CATEGORY_ALIASES = {
    "еда": "Еда",
    "продукты": "Еда",
    "кафе": "Развлечения",
    "транспорт": "Транспорт",
    "электроника": "Электроника",
    "одежда": "Одежда",
    "здоровье": "Здоровье",
    "аптека": "Здоровье",
    "развлечения": "Развлечения",
    "коммунальные услуги": "Коммунальные услуги",
    "дом и ремонт": "Коммунальные услуги",
    "прочее": "Прочее",
}

DB_CATEGORY_MAP = {
    "Еда": "Продукты",
    "Здоровье": "Аптека",
    "Развлечения": "Кафе",
    "Коммунальные услуги": "Дом и ремонт",
    "Транспорт": "Транспорт",
    "Электроника": "Электроника",
    "Одежда": "Одежда",
    "Прочее": "Прочее",
}


def _parse_amount(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        amount = Decimal(str(value))
    elif isinstance(value, str):
        cleaned = (
            value.strip()
            .replace(" ", "")
            .replace("\u00a0", "")
            .replace(",", ".")
        )
        if not cleaned:
            return None
        try:
            amount = Decimal(cleaned)
        except InvalidOperation:
            return None
    else:
        return None
    if amount <= 0:
        return None
    return amount.quantize(Decimal("0.01"))


def _parse_date(value: Any, *, today: date | None = None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        try:
            parsed = date.fromisoformat(text[:10])
        except ValueError:
            return None
    else:
        return None

    reference = today or date.today()
    if parsed < reference - timedelta(days=15 * 365):
        return None
    if parsed > reference + timedelta(days=1):
        return None
    return parsed


def _parse_currency(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip().upper()
    if len(text) != 3 or not text.isalpha():
        return None
    return text


def _parse_category(
    value: Any,
    *,
    allowed: list[str],
    db_names: set[str],
) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    if text in db_names:
        return text

    canonical = text if text in allowed else CATEGORY_ALIASES.get(text.lower())
    if canonical is None:
        return None

    mapped = DB_CATEGORY_MAP.get(canonical, canonical)
    if not db_names or mapped in db_names or mapped == "Прочее":
        return mapped
    return None


def _parse_items(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    items: list[dict] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if not name or not str(name).strip():
            continue
        price = _parse_amount(row.get("price"))
        quantity_raw = row.get("quantity", 1)
        try:
            quantity = float(quantity_raw)
        except (TypeError, ValueError):
            quantity = 1.0
        if quantity <= 0:
            quantity = 1.0
        items.append(
            {
                "name": str(name).strip(),
                "price": float(price) if price is not None else None,
                "quantity": quantity,
            }
        )
    return items


def _parse_confidence(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"high", "medium", "low"}:
        return text
    return "low"


def validate_ollama_payload(
    payload: dict[str, Any],
    *,
    db_category_names: list[str] | None = None,
    today: date | None = None,
) -> dict:
    allowed = list(ALLOWED_CATEGORIES)
    db_names = set(db_category_names or [])

    amount = _parse_amount(payload.get("amount"))
    purchase_date = _parse_date(payload.get("date"), today=today)
    currency = _parse_currency(payload.get("currency"))
    merchant_raw = payload.get("merchant_name")
    merchant_name = None
    if merchant_raw is not None and str(merchant_raw).strip():
        merchant_name = str(merchant_raw).strip()[:255]

    category = _parse_category(
        payload.get("category"),
        allowed=allowed,
        db_names=db_names,
    )
    confidence = _parse_confidence(payload.get("confidence"))
    items = _parse_items(payload.get("items"))

    amount_confident = amount is not None
    date_confident = purchase_date is not None
    merchant_confident = merchant_name is not None
    all_key_fields_missing = (
        not amount_confident and not date_confident and not merchant_confident
    )
    needs_manual_review = (
        confidence == "low"
        or all_key_fields_missing
        or (amount is None and merchant_name is None)
    )

    matched = "llm"
    return {
        "amount": amount,
        "currency": currency,
        "merchant_name": merchant_name,
        "purchase_date": purchase_date,
        "category": category,
        "items": items,
        "llm_confidence": confidence,
        "needs_manual_review": needs_manual_review,
        "all_key_fields_missing": all_key_fields_missing,
        "amount_matched_by": matched if amount_confident else "none",
        "date_matched_by": matched if date_confident else "none",
        "merchant_matched_by": matched if merchant_confident else "none",
        "amount_source": matched if amount_confident else "none",
        "merchant_source": matched if merchant_confident else "none",
        "date_source": matched if date_confident else "none",
        "amount_confident": amount_confident,
        "date_confident": date_confident,
        "merchant_confident": merchant_confident,
        "parser_mode": "llm",
    }


def empty_manual_review_result(*, reason: str) -> dict:
    return {
        "amount": None,
        "currency": None,
        "merchant_name": None,
        "purchase_date": None,
        "category": None,
        "items": [],
        "llm_confidence": "low",
        "needs_manual_review": True,
        "all_key_fields_missing": True,
        "amount_matched_by": "none",
        "date_matched_by": "none",
        "merchant_matched_by": "none",
        "amount_source": "none",
        "merchant_source": "none",
        "date_source": "none",
        "amount_confident": False,
        "date_confident": False,
        "merchant_confident": False,
        "parser_mode": "llm",
        "parser_error": reason,
    }
