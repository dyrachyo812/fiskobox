import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400
    detail = "Ошибка запроса"

    def __init__(self, detail: str | None = None) -> None:
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class AuthError(AppError):
    status_code = 401
    detail = "Не авторизован"


class NotFoundError(AppError):
    status_code = 404
    detail = "Не найдено"


class ForbiddenError(AppError):
    status_code = 403
    detail = "Доступ запрещён"


class InvalidLinkCodeError(AppError):
    status_code = 400
    detail = "Неверный или просроченный код"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Необработанная ошибка на %s", request.url.path)
        return JSONResponse(
            status_code=500, content={"detail": "Внутренняя ошибка сервера"}
        )
