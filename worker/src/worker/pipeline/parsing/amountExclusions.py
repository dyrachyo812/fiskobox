import re

MULTIPLY_LINE = re.compile(
    r"\d+[.]?\s*[xх×X]\s*[\d\sOОoо.,]+\s*=",
)

NON_MONEY_LABEL = re.compile(
    r"(?:"
    r"\bинн\b|\bінн\b|\bпн\b|\bінн\b|"
    r"терминал|термінал|terminal|"
    r"код\s*авториза|auth(?:orization)?\s*code|"
    r"\bфн\b|\bфд\b|\bфп\b|рн\s*ккт|"
    r"заводськ|заводск|\bзн\b|"
    r"смен[аыіи]|чек\s*(?:№|n|no|номер)|"
    r"карт[аыі]?[\s*]*\*+|\*+\s*\d{2,4}|"
    r"rrn|approval\s*code"
    r")",
    re.IGNORECASE,
)

LONG_ID_NUMBER = re.compile(r"(?<!\d)\d{8,}(?!\d)")
MASKED_CARD = re.compile(r"\*+\d{2,4}|\d{2,4}\*+")
FISCAL_LABELED_NUMBER = re.compile(
    r"(?:инн|інн|пн|фн|фд|фп|зн|терминал|термінал|terminal|rrn)"
    r"\s*[:№#]?\s*[\dOoОоIlІі]{6,}",
    re.IGNORECASE,
)


def is_multiply_line(line: str) -> bool:
    return MULTIPLY_LINE.search(line) is not None


def is_non_money_line(line: str) -> bool:
    lowered = line.lower()
    if FISCAL_LABELED_NUMBER.search(line):
        if not re.search(
            r"(сум[ама]|иог|итог|total|разом|всього|сплати|оплат)",
            lowered,
            re.IGNORECASE,
        ):
            return True
    if NON_MONEY_LABEL.search(line) and not re.search(
        r"(сум[ама]|итог|total|разом|всього|сплати|к\s*оплат)",
        lowered,
        re.IGNORECASE,
    ):
        return True
    return False


def is_excluded_amount_token(token: str, line: str) -> bool:
    digits = re.sub(r"\D", "", token)
    if len(digits) >= 10:
        return True
    if MASKED_CARD.search(token) or MASKED_CARD.search(line):
        if "*" in token or "*" in line:
            token_digits = re.sub(r"\D", "", token)
            if len(token_digits) <= 4:
                return True
    if LONG_ID_NUMBER.fullmatch(digits) and "." not in token and "," not in token:
        return True
    if FISCAL_LABELED_NUMBER.search(line):
        labeled = FISCAL_LABELED_NUMBER.search(line)
        if labeled and token.strip() in labeled.group(0):
            return True
    return False
