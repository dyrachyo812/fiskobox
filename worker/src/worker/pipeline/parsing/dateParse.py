import re
from datetime import date, datetime

NUMERIC_DATE_TOKEN = re.compile(
    r"(?<!\d)(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})\.?(?!\d)"
)
ISO_DATE_TOKEN = re.compile(r"(?<!\d)(\d{4}[.\-/]\d{2}[.\-/]\d{2})(?!\d)")
TIME_TOKEN = re.compile(
    r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]?\d(?::[0-5]?\d)?(?!\d)"
)
DATE_THEN_TIME = re.compile(
    r"(?<!\d)(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})\.?"
    r"\s+"
    r"(?:[01]?\d|2[0-3]):[0-5]?\d(?::[0-5]?\d)?(?!\d)"
)
TIME_THEN_DATE = re.compile(
    r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]?\d(?::[0-5]?\d)?"
    r"\s+"
    r"(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{2,4})\.?(?!\d)"
)

NUMERIC_FORMATS = (
    "%d.%m.%Y",
    "%d.%m.%y",
    "%Y.%m.%d",
)

MONTH_MAP = {
    "января": 1,
    "январь": 1,
    "янв": 1,
    "февраля": 2,
    "февраль": 2,
    "фев": 2,
    "марта": 3,
    "март": 3,
    "мар": 3,
    "апреля": 4,
    "апрель": 4,
    "апр": 4,
    "мая": 5,
    "май": 5,
    "июня": 6,
    "июнь": 6,
    "июн": 6,
    "июля": 7,
    "июль": 7,
    "июл": 7,
    "августа": 8,
    "август": 8,
    "авг": 8,
    "сентября": 9,
    "сентябрь": 9,
    "сен": 9,
    "октября": 10,
    "октябрь": 10,
    "окт": 10,
    "ноября": 11,
    "ноябрь": 11,
    "ноя": 11,
    "декабря": 12,
    "декабрь": 12,
    "дек": 12,
    "січня": 1,
    "січень": 1,
    "лютого": 2,
    "лютий": 2,
    "березня": 3,
    "березень": 3,
    "квітня": 4,
    "квітень": 4,
    "травня": 5,
    "травень": 5,
    "червня": 6,
    "червень": 6,
    "липня": 7,
    "липень": 7,
    "серпня": 8,
    "серпень": 8,
    "вересня": 9,
    "вересень": 9,
    "жовтня": 10,
    "жовтень": 10,
    "листопада": 11,
    "листопад": 11,
    "грудня": 12,
    "грудень": 12,
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

MONTH_ALTERNATION = "|".join(sorted(MONTH_MAP, key=len, reverse=True))
TEXT_DATE_PATTERN = re.compile(
    rf"\b(\d{{1,2}})\s+({MONTH_ALTERNATION})\s+(\d{{2,4}})\b",
    re.IGNORECASE,
)


def year_bounds(today: date | None = None) -> tuple[int, int]:
    current = today or date.today()
    return current.year - 15, current.year + 1


def is_plausible(parsed: date, today: date | None = None) -> bool:
    min_year, max_year = year_bounds(today)
    if not (min_year <= parsed.year <= max_year):
        return False
    if not (1 <= parsed.month <= 12):
        return False
    if not (1 <= parsed.day <= 31):
        return False
    return True


def parse_token(token: str, today: date | None = None) -> date | None:
    normalized = token.strip().rstrip(".").replace("-", ".").replace("/", ".")
    for pattern in NUMERIC_FORMATS:
        try:
            parsed = datetime.strptime(normalized, pattern).date()
        except ValueError:
            continue
        if is_plausible(parsed, today):
            return parsed
    return None


def parse_text_date(
    day: str,
    month_name: str,
    year: str,
    today: date | None = None,
) -> date | None:
    month = MONTH_MAP.get(month_name.lower())
    if month is None:
        return None
    year_value = int(year)
    if year_value < 100:
        year_value += 2000
    try:
        parsed = date(year_value, month, int(day))
    except ValueError:
        return None
    return parsed if is_plausible(parsed, today) else None


def line_has_time(line: str) -> bool:
    return TIME_TOKEN.search(line) is not None


def dates_with_time_on_line(line: str, today: date | None = None) -> list[date]:
    found: list[date] = []
    for pattern in (DATE_THEN_TIME, TIME_THEN_DATE):
        for token in pattern.findall(line):
            parsed = parse_token(token, today)
            if parsed is not None:
                found.append(parsed)
    return found


def dates_on_line(line: str, today: date | None = None) -> list[date]:
    found: list[date] = []
    for token in NUMERIC_DATE_TOKEN.findall(line):
        parsed = parse_token(token, today)
        if parsed is not None:
            found.append(parsed)
    for token in ISO_DATE_TOKEN.findall(line):
        parsed = parse_token(token, today)
        if parsed is not None:
            found.append(parsed)
    for day, month_name, year in TEXT_DATE_PATTERN.findall(line):
        parsed = parse_text_date(day, month_name, year, today)
        if parsed is not None:
            found.append(parsed)
    return found
