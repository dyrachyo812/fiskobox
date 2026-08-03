import re

NON_DATE_LABEL = re.compile(
    r"(?:"
    r"\bинн\b|\bінн\b|\bпн\b|"
    r"терминал|термінал|terminal|"
    r"код\s*авториза|auth(?:orization)?\s*code|"
    r"\bфн\b|\bфд\b|\bфп\b|рн\s*ккт|"
    r"\bзн\b|заводськ|заводск|"
    r"срок\s*действ|термін\s*ді[їи]|valid\s*until|"
    r"rrn|approval\s*code"
    r")",
    re.IGNORECASE,
)

LONG_ID_CONTEXT = re.compile(
    r"(?:инн|інн|пн|фн|фд|фп|зн|терминал|термінал|terminal)"
    r"\s*[:№#]?\s*[\dOoОоIlІі.\-/]{6,}",
    re.IGNORECASE,
)

PRINT_KEYWORDS = ("печат", "отпеч", "надруков", "printed")
OPERATION_KEYWORDS = (
    "дата покуп",
    "дата операц",
    "дата оплат",
    "дата чек",
    "час операц",
    "purchase date",
    "operation date",
    "transaction date",
    "дата:",
    "date:",
)
DATE_HINT_KEYWORDS = (
    "дата",
    "date",
    "час",
    "time",
    "покуп",
    "оплат",
    "операц",
)


def is_non_date_line(line: str) -> bool:
    if LONG_ID_CONTEXT.search(line):
        return True
    lowered = line.lower()
    if NON_DATE_LABEL.search(line) and not any(
        keyword in lowered for keyword in ("дата", "date", "час", "time")
    ):
        return True
    return False


def is_print_line(line: str) -> bool:
    lowered = line.lower()
    return any(keyword in lowered for keyword in PRINT_KEYWORDS)


def is_operation_line(line: str) -> bool:
    lowered = line.lower()
    return any(keyword in lowered for keyword in OPERATION_KEYWORDS)


def is_hint_line(line: str) -> bool:
    lowered = line.lower()
    return any(keyword in lowered for keyword in DATE_HINT_KEYWORDS)
