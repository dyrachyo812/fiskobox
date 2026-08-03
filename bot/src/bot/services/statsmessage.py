def format_stats(summary: dict) -> str:
    if not summary["by_category"]:
        return "За этот месяц трат пока нет."

    lines = [f"Траты за {summary['month'].strftime('%m.%Y')}:"]
    # Сортируем категории по убыванию суммы — самое дорогое сверху.
    for category, amount in sorted(
        summary["by_category"], key=lambda item: item[1], reverse=True
    ):
        lines.append(f"• {category}: {amount}")
    lines.append(f"Итого: {summary['total']}")
    return "\n".join(lines)
