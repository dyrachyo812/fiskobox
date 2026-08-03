from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.logging import configure_logging

from backend.api.routes import analytics, auth, categories, documents, health
from backend.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="PaperlessBox API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
    app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

    return app


app = create_app()
