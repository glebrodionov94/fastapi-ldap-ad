from fastapi import FastAPI

from app.api.v1.users import router as users_router
from app.api.v1.groups import router as groups_router
from app.api.v1.ous import router as ous_router
from app.api.v1.containers import router as containers_router
from app.api.v1.auth import router as auth_router
from app.core.config import settings
from app.core.logging import setup_logging


def get_app() -> FastAPI:
    setup_logging(settings.debug)

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="REST API для управления Active Directory: пользователи, группы, подразделения",
    )

    @app.get("/health", tags=["Система"])
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(groups_router)
    app.include_router(ous_router)
    app.include_router(containers_router)

    return app


app = get_app()
