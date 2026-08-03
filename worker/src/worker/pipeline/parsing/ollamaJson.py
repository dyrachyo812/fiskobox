import json
import re
from typing import Any


class OllamaJsonError(Exception):
    pass


_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json_object(text: str) -> dict[str, Any]:
    if not text or not text.strip():
        raise OllamaJsonError("пустой ответ модели")

    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence:
        try:
            parsed = json.loads(fence.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    match = _JSON_OBJECT_RE.search(stripped)
    if not match:
        raise OllamaJsonError("в ответе нет JSON-объекта")

    candidate = match.group(0)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as error:
        raise OllamaJsonError("невалидный JSON в ответе модели") from error

    if not isinstance(parsed, dict):
        raise OllamaJsonError("JSON должен быть объектом")
    return parsed
