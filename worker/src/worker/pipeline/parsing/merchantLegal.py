import re

from worker.pipeline.parsing.merchantFilters import clean_merchant

LEGAL_WITH_QUOTES = re.compile(
    r"(?P<form>ООО|ОАО|ЗАО|ПАО|АО|ТОВ|ТЗОВ|ИП|ФОП|ПП|ПІІ|ППІ|ФЛП|LLC|LTD)"
    r"\s*[\"«'](?P<name>[^\"«»']{3,80})[\"»']",
    re.IGNORECASE,
)

LEGAL_PLAIN = re.compile(
    r"(?P<form>ООО|ОАО|ЗАО|ПАО|АО|ТОВ|ТЗОВ|ИП|ФОП|ПП|ПІІ|ППІ|ФЛП)"
    r"\s+(?P<name>[A-Za-zА-Яа-яІіЇїЄєҐґ][\w.\-]*(?:\s+[A-Za-zА-Яа-яІіЇїЄєҐґ][\w.\-]*){0,5})",
    re.IGNORECASE,
)

OCR_OOO_QUOTES = re.compile(
    r"\b0{2,3}\s*[\"«](?P<name>[^\"«»]{3,80})[\"»]"
)

QUOTED_NAME = re.compile(
    r"[\"«](?P<name>[A-Za-zА-Яа-яІіЇїЄєҐґ][^\"«»]{2,80})[\"»]"
)


def _format_legal(form: str, name: str) -> str | None:
    cleaned_name = clean_merchant(name)
    if cleaned_name is None:
        return None
    form_norm = form.upper().replace("ППІ", "ПІІ")
    if form_norm in {"LLC", "LTD"}:
        return clean_merchant(f'{form_norm} "{cleaned_name}"')
    return clean_merchant(f'{form_norm} "{cleaned_name}"')


def extract_legal_merchant(line: str) -> str | None:
    match = LEGAL_WITH_QUOTES.search(line)
    if match:
        formatted = _format_legal(match.group("form"), match.group("name"))
        if formatted is not None:
            return formatted

    ocr = OCR_OOO_QUOTES.search(line)
    if ocr:
        formatted = _format_legal("ООО", ocr.group("name"))
        if formatted is not None:
            return formatted

    match = LEGAL_PLAIN.search(line)
    if match:
        name = match.group("name").strip()
        if re.search(r"\d{4,}", name):
            return None
        form = match.group("form")
        cleaned = clean_merchant(f"{form} {name}")
        return cleaned

    quoted = QUOTED_NAME.search(line)
    if quoted and re.search(r"\b(?:ооо|тов|000)\b", line, re.IGNORECASE):
        return _format_legal("ООО", quoted.group("name"))

    return None
