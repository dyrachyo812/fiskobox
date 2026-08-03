import re

from worker.pipeline.parsing.merchantKnown import normalize_text

MIN_LENGTH = 3
MAX_LENGTH = 255

SERVICE_WORDS = {
    "чек",
    "каса",
    "кассовый",
    "касовий",
    "фискальный",
    "фіскальний",
    "фискальн",
    "фіскальн",
    "оператор",
    "терминал",
    "термінал",
    "terminal",
    "магазин",
    "товар",
    "разом",
    "сума",
    "сумма",
    "итого",
    "итог",
    "всього",
    "всего",
    "готівка",
    "наличные",
    "картка",
    "карта",
    "україна",
    "украина",
    "россия",
    "росія",
    "ukraine",
    "russia",
    "atlas",
    "online",
    "true",
}

SERVICE_PHRASES = (
    "кассовый чек",
    "касовий чек",
    "фискальный чек",
    "фіскальний чек",
    "чек получен",
    "спасибо за покупку",
    "дякуємо за покупку",
)

SKIP_LINE = re.compile(
    r"(?:"
    r"^\d+$|"
    r"\b(?:пн|зн|фн|фд|фп|інн|инн|ід|id|fn|zn|pn)\b\s*[:.]?\s*[\dOoОо]|"
    r"^(?:каса|оператор|чек|фіскальн|фискальн|разом|сума|сумма|итого|итог|пдв|ндс)\b|"
    r"^(?:товар\d*|товар|замін|замен|екстра|экстра|гарант|картка|карта|готівка|налич)\b|"
    r"^(?:україна|украина|россия|росія|ukraine|russia)$|"
    r"^(?:м\.|місто|город|вул\.|ул\.|просп\.|пр\.)\b|"
    r"^\d{5,6}\b|"
    r"^\d+[.,]\d{2}\b|"
    r"\d+\s*[xх×]|"
    r"=\s*\d|"
    r"\b\d{2,}\s*(?:gb|гб|tb|шт)\b|"
    r"\d{3,}\s*[.,]\s*\d{2}|"
    r"терминал|термінал|terminal|"
    r"код\s*авториза|"
    r"форма\s*оплат|форми\s*оплат"
    r")",
    re.IGNORECASE,
)

DATE_LINE = re.compile(
    r"(?<!\d)\d{1,2}[./-]\d{1,2}[./-]\d{2,4}(?!\d)"
    r"|"
    r"(?<!\d)\d{4}[./-]\d{2}[./-]\d{2}(?!\d)"
)

ADDRESS_LINE = re.compile(
    r"(?:"
    r"\b(?:вул|ул|просп|пр|бул|пер)\.?\b|"
    r"\b(?:м\.|місто|город)\b|"
    r"\b\d{5,6}\b"
    r")",
    re.IGNORECASE,
)


def is_service_only(text: str) -> bool:
    lowered = normalize_text(text)
    compact = re.sub(r"[^\w\s]", " ", lowered, flags=re.UNICODE)
    compact = re.sub(r"\s+", " ", compact).strip()
    if not compact:
        return True
    if compact in SERVICE_PHRASES or compact in SERVICE_WORDS:
        return True
    words = [word for word in compact.split() if word]
    if not words:
        return True
    return all(word in SERVICE_WORDS for word in words)


def looks_like_ocr_garbage(line: str) -> bool:
    cleaned = line.strip()
    if not cleaned:
        return True
    if re.search(r"[=\-~_|]{2,}", cleaned):
        return True
    letters = sum(character.isalpha() for character in cleaned)
    if letters / max(len(cleaned), 1) < 0.45:
        return True
    weird = sum(character in "=~_|<>[]{}*" for character in cleaned)
    if weird >= 2:
        return True
    return False


def is_skipped_line(line: str) -> bool:
    cleaned = line.strip()
    if not cleaned:
        return True
    if looks_like_ocr_garbage(cleaned):
        return True
    if DATE_LINE.fullmatch(cleaned.strip(" .")):
        return True
    if ADDRESS_LINE.search(cleaned) and not re.search(
        r"\b(?:ооо|тов|ип|фоп|тзов|000)\b",
        cleaned,
        re.IGNORECASE,
    ):
        if sum(character.isalpha() for character in cleaned) < 12:
            return True
    letters = sum(character.isalpha() for character in cleaned)
    if letters < MIN_LENGTH:
        return True
    digit_ratio = sum(character.isdigit() for character in cleaned) / max(len(cleaned), 1)
    if digit_ratio > 0.55:
        return True
    return SKIP_LINE.search(cleaned) is not None


def is_plausible_merchant_name(text: str) -> bool:
    if not text or len(text) < MIN_LENGTH:
        return False
    if is_service_only(text):
        return False
    tokens = re.findall(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]+", text)
    if not tokens:
        return False
    longest = max(len(token) for token in tokens)
    if longest < 5:
        return False
    short = sum(1 for token in tokens if len(token) <= 2)
    if short >= 2 and short >= len(tokens) / 2:
        return False
    if len(tokens) >= 3 and longest <= 5:
        tiny = sum(1 for token in tokens if len(token) <= 3)
        if tiny >= 2:
            return False
    has_latin = any(re.search(r"[A-Za-z]", token) for token in tokens)
    has_cyrillic = any(re.search(r"[А-Яа-яІіЇїЄєҐґ]", token) for token in tokens)
    if has_latin and has_cyrillic:
        latin_long = [
            token for token in tokens if re.fullmatch(r"[A-Za-z]+", token) and len(token) >= 5
        ]
        cyr_long = [
            token
            for token in tokens
            if re.search(r"[А-Яа-яІіЇїЄєҐґ]", token) and len(token) >= 5
        ]
        if latin_long and cyr_long:
            return False
        if not latin_long and not cyr_long:
            return False
        if not latin_long and tiny_mixed_prefix(tokens):
            return False
    letters = sum(character.isalpha() for character in text)
    if letters / max(len(text), 1) < 0.5:
        return False
    return True


def tiny_mixed_prefix(tokens: list[str]) -> bool:
    if len(tokens) < 2:
        return False
    head = tokens[:-1]
    return all(len(token) <= 3 for token in head)


def clean_merchant(raw: str) -> str | None:
    text = raw.strip()
    text = text.replace("«", '"').replace("»", '"')
    text = re.sub(r"^[\s=\-~_|.,:;!?#*<>]+", "", text)
    text = re.sub(r"[\s=\-~_|.,:;!?#*<>]+$", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    words: list[str] = []
    for word in text.split(" "):
        if not word:
            continue
        letters = sum(character.isalpha() for character in word)
        if letters == 0:
            if re.fullmatch(r"0{2,3}", word):
                words.append("ООО")
                continue
            if word in {'"', "'"}:
                words.append(word)
                continue
            continue
        if letters == 1 and len(word) <= 2:
            continue
        if re.fullmatch(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]\W*", word) and letters == 1:
            continue
        words.append(word)

    text = " ".join(words).strip()
    text = re.sub(r'\s+"', ' "', text)
    text = re.sub(r'"\s+', '"', text)
    text = re.sub(r"\s+", " ", text).strip(" -~,")
    if len(text) < MIN_LENGTH:
        return None
    if is_service_only(text):
        return None
    return text[:MAX_LENGTH]
