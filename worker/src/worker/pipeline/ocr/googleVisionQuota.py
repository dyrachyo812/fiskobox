from datetime import datetime, timezone

from shared.logging import get_logger

logger = get_logger(__name__)

KEY_PREFIX = "google_vision:requests:"


class GoogleVisionQuotaError(Exception):
    pass


class GoogleVisionQuota:
    def __init__(
        self,
        redis_client,
        *,
        monthly_limit: int = 1000,
        warn_threshold: int = 900,
        enforce_limit: bool = True,
    ) -> None:
        self.redis_client = redis_client
        self.monthly_limit = monthly_limit
        self.warn_threshold = warn_threshold
        self.enforce_limit = enforce_limit

    def month_key(self, when: datetime | None = None) -> str:
        moment = when or datetime.now(timezone.utc)
        return f"{KEY_PREFIX}{moment.strftime('%Y-%m')}"

    def current_count(self) -> int:
        try:
            raw = self.redis_client.get(self.month_key())
        except Exception as error:
            logger.warning(
                "Google Vision quota read failed",
                extra={"error": str(error)},
            )
            return 0
        if raw is None:
            return 0
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0

    def remaining(self) -> int:
        return max(0, self.monthly_limit - self.current_count())

    def is_near_limit(self, count: int | None = None) -> bool:
        value = self.current_count() if count is None else count
        return value >= self.warn_threshold

    def is_exhausted(self, count: int | None = None) -> bool:
        value = self.current_count() if count is None else count
        return value >= self.monthly_limit

    def ensure_available(self) -> None:
        count = self.current_count()
        if self.is_near_limit(count):
            logger.warning(
                "Google Vision monthly usage near free-tier limit",
                extra={
                    "google_vision_used": count,
                    "google_vision_limit": self.monthly_limit,
                    "google_vision_remaining": max(0, self.monthly_limit - count),
                },
            )
        if self.enforce_limit and self.is_exhausted(count):
            raise GoogleVisionQuotaError(
                f"исчерпан бесплатный лимит Google Vision "
                f"({count}/{self.monthly_limit} за месяц)"
            )

    def record_usage(self) -> int:
        key = self.month_key()
        try:
            count = int(self.redis_client.incr(key))
            if count == 1:
                self.redis_client.expire(key, 40 * 24 * 60 * 60)
        except Exception as error:
            logger.warning(
                "Google Vision quota increment failed",
                extra={"error": str(error)},
            )
            return self.current_count()

        if self.is_near_limit(count):
            logger.warning(
                "Google Vision monthly usage near free-tier limit",
                extra={
                    "google_vision_used": count,
                    "google_vision_limit": self.monthly_limit,
                    "google_vision_remaining": max(0, self.monthly_limit - count),
                },
            )
        else:
            logger.info(
                "Google Vision request counted",
                extra={
                    "google_vision_used": count,
                    "google_vision_limit": self.monthly_limit,
                    "google_vision_remaining": max(0, self.monthly_limit - count),
                },
            )
        return count
