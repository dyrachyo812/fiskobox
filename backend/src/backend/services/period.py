from datetime import date, timedelta


def period_start(period: str) -> date:
    today = date.today()
    if period == "week":
        return today - timedelta(days=today.weekday())
    if period == "year":
        return today.replace(month=1, day=1)
    return today.replace(day=1)
