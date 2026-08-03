import json
import urllib.error
import urllib.request
from typing import Any


class OllamaError(Exception):
    pass


class OllamaClient:
    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "llama3.1:8b",
        timeout_seconds: float = 20.0,
        temperature: float = 0.1,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

    def generate(self, prompt: str, *, use_json_format: bool = True) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if use_json_format:
            payload["format"] = "json"

        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except TimeoutError as error:
            raise OllamaError(
                f"таймаут Ollama ({self.timeout_seconds}s)"
            ) from error
        except urllib.error.URLError as error:
            raise OllamaError(f"Ollama недоступна: {error.reason}") from error
        except Exception as error:
            raise OllamaError(f"ошибка Ollama API: {error}") from error

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise OllamaError("Ollama вернула невалидный envelope") from error

        text = data.get("response")
        if not isinstance(text, str) or not text.strip():
            raise OllamaError("Ollama вернула пустой response")
        return text
