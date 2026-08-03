from shared.logging import get_logger
from shared.models import Category

from worker.pipeline.parsing.ollamaClient import OllamaClient, OllamaError
from worker.pipeline.parsing.ollamaJson import OllamaJsonError, extract_json_object
from worker.pipeline.parsing.ollamaPrompt import build_receipt_prompt
from worker.pipeline.parsing.ollamaValidate import (
    empty_manual_review_result,
    validate_ollama_payload,
)

logger = get_logger(__name__)

MAX_ATTEMPTS = 2


class OllamaReceiptParser:
    def __init__(self, client: OllamaClient) -> None:
        self.client = client

    def parse(self, raw_text: str, categories: list[Category]) -> dict:
        db_names = [category.name for category in categories]
        prompt = build_receipt_prompt(raw_text)
        last_error = "unknown"

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response_text = self.client.generate(prompt, use_json_format=True)
                payload = extract_json_object(response_text)
                result = validate_ollama_payload(
                    payload,
                    db_category_names=db_names,
                )
                logger.info(
                    "Ollama receipt parse succeeded",
                    extra={
                        "attempt": attempt,
                        "llm_confidence": result.get("llm_confidence"),
                        "needs_manual_review": result.get("needs_manual_review"),
                    },
                )
                return result
            except (OllamaError, OllamaJsonError, ValueError, TypeError) as error:
                last_error = str(error)
                logger.warning(
                    "Ollama receipt parse attempt failed",
                    extra={"attempt": attempt, "error": last_error},
                )

        logger.warning(
            "Ollama receipt parse exhausted attempts",
            extra={"attempts": MAX_ATTEMPTS, "error": last_error},
        )
        return empty_manual_review_result(
            reason=f"невалидный JSON после {MAX_ATTEMPTS} попыток: {last_error}"
        )
