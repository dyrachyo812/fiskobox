import re
from decimal import Decimal, InvalidOperation

OCR_DIGIT_CHARS = "0-9OoОоIlІі|"
AMOUNT_TOKEN = re.compile(
    r"(?<![0-9A-Za-zА-Яа-яЁёІіЇїЄєҐґ])"
    r"(?:[$€₴₽]\s*)?"
    rf"[0-9IlІі|][{OCR_DIGIT_CHARS}\s.,]*[0-9]"
    r"(?:\s*[$€₴₽])?"
)

OCR_DIGIT_MAP = {
    "O": "0",
    "o": "0",
    "О": "0",
    "о": "0",
    "I": "1",
    "l": "1",
    "|": "1",
    "І": "1",
    "і": "1",
}


def fix_ocr_digits(token: str) -> str:
    return "".join(OCR_DIGIT_MAP.get(character, character) for character in token)


def has_digit(token: str) -> bool:
    return any(character.isdigit() for character in token)


def real_digit_count(token: str) -> int:
    return sum(character.isdigit() for character in token)


def strip_currency_marks(raw: str) -> str:
    return re.sub(r"[$€₴₽]", "", raw).strip()


def normalize_amount(raw: str, *, allow_plain_integer: bool = True) -> Decimal | None:
    if not has_digit(raw):
        return None
    if real_digit_count(raw) < 2:
        return None
    if "/" in raw:
        return None

    cleaned = strip_currency_marks(raw)
    cleaned = fix_ocr_digits(cleaned)
    cleaned = re.sub(r"[.,]\s+(?=\d)", ".", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    no_spaces = cleaned.replace(" ", "")
    if ".." in no_spaces or ",," in no_spaces or ".," in no_spaces or ",." in no_spaces:
        return None
    if "," in no_spaces and "." in no_spaces:
        if no_spaces.rfind(",") > no_spaces.rfind("."):
            no_spaces = no_spaces.replace(".", "").replace(",", ".")
        else:
            no_spaces = no_spaces.replace(",", "")
    elif "," in no_spaces:
        parts = no_spaces.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            no_spaces = f"{parts[0]}.{parts[1]}"
        elif len(parts) > 2 and len(parts[-1]) <= 2:
            no_spaces = "".join(parts[:-1]) + "." + parts[-1]
        else:
            no_spaces = no_spaces.replace(",", "")
    elif "." in no_spaces:
        parts = no_spaces.split(".")
        if any(part == "" for part in parts):
            return None
        if len(parts) > 2 and len(parts[-1]) <= 2:
            no_spaces = "".join(parts[:-1]) + "." + parts[-1]

    try:
        value = Decimal(no_spaces)
    except InvalidOperation:
        return None

    if value <= 0 or value >= Decimal(1000000):
        return None

    if "." in no_spaces:
        fraction = no_spaces.split(".")[-1]
        if len(fraction) > 2:
            return None

    digit_body = re.sub(r"\D", "", no_spaces)
    if "." not in no_spaces and digit_body.startswith("0") and len(digit_body) >= 3:
        return None
    if "." not in no_spaces and not allow_plain_integer:
        return None
    return value


def find_amount_tokens(line: str) -> list[tuple[str, int]]:
    return [(match.group(0), match.start()) for match in AMOUNT_TOKEN.finditer(line)]


def normalize(raw: str, *, allow_plain_integer: bool = True) -> Decimal | None:
    return normalize_amount(raw, allow_plain_integer=allow_plain_integer)
