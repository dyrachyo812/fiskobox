from dataclasses import dataclass, field


@dataclass(frozen=True)
class WordConfidence:
    text: str
    confidence: float


@dataclass
class OCRResult:
    raw_text: str
    confidence: float | None
    words_with_confidence: list[WordConfidence] = field(default_factory=list)
    provider: str = "unknown"
    used_fallback: bool = False
    fallback_reason: str | None = None
