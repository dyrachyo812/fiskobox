from worker.pipeline.parsing.currency import format_currency_label

FIELD_LABELS = {
    "merchant_name": "Продавец",
    "amount": "Сумма",
    "purchase_date": "Дата",
    "category": "Категория",
}

GENERIC_FAILURE_MESSAGE = (
    "Не удалось обработать чек, попробуйте снова или введите данные вручную в веб-панели"
)

MANUAL_ENTRY_PROMPT = (
    "Не удалось уверенно распознать чек.\n"
    "Введите данные вручную в веб-панели: продавец, сумма и дата."
)


def success_message(parsed: dict, *, low_sharpness: bool = False) -> str:
    if parsed.get("all_key_fields_missing"):
        lines = [MANUAL_ENTRY_PROMPT]
        if low_sharpness or parsed.get("low_quality_scan"):
            lines.append("")
            lines.append("Фото нечёткое — лучше переснять при хорошем свете.")
        return "\n".join(lines)

    lines = ["Готово, чек распознан:"]

    merchant = parsed.get("merchant_name") if parsed.get("merchant_confident") else None
    lines.append(f"Продавец: {merchant}" if merchant else "Продавец: не найден")

    amount = parsed.get("amount") if parsed.get("amount_confident") else None
    currency = format_currency_label(parsed.get("currency"))
    if amount is not None:
        lines.append(f"Сумма: {amount} {currency}".strip())
    else:
        lines.append("Сумма: не найдена")

    purchase_date = (
        parsed.get("purchase_date") if parsed.get("date_confident") else None
    )
    lines.append(f"Дата: {purchase_date}" if purchase_date else "Дата: не найдена")

    category = parsed.get("category")
    lines.append(f"Категория: {category}" if category else "Категория: не определена")

    missing = []
    if not parsed.get("merchant_confident"):
        missing.append("merchant_name")
    if not parsed.get("amount_confident"):
        missing.append("amount")
    if not parsed.get("date_confident"):
        missing.append("purchase_date")

    if missing:
        labels = ", ".join(FIELD_LABELS[key] for key in missing)
        lines.append("")
        lines.append(
            f"Не удалось разобрать: {labels}. Введите недостающие данные вручную в веб-панели."
        )

    if parsed.get("needs_manual_review"):
        lines.append("")
        reasons = []
        if parsed.get("amount_matched_by") == "ambiguous":
            reasons.append("сумма неоднозначна")
        if parsed.get("merchant_matched_by") == "rejected":
            reasons.append("продавец не распознан")
        if not reasons:
            reasons.append("проверьте поля вручную")
        lines.append("Требует ручной проверки: " + ", ".join(reasons) + ".")

    if low_sharpness or parsed.get("low_quality_scan"):
        lines.append("")
        lines.append("Низкое качество скана: фото нечёткое, распознавание может быть неточным.")

    return "\n".join(lines)


def failure_message(reason: str) -> str:
    return (
        f"Не удалось распознать чек: {reason}.\n"
        "Сфотографируйте чек при хорошем освещении без бликов и сгибов "
        "или введите данные вручную в веб-панели."
    )
