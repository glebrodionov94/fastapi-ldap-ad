from fastapi import FastAPI, Depends

from app.api.v1.users import router as users_router
from app.api.v1.groups import router as groups_router
from app.api.v1.ous import router as ous_router
from app.api.v1.containers import router as containers_router
from app.api.v1.auth import router as auth_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.security import get_current_user


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
    app.include_router(users_router, dependencies=[Depends(get_current_user)])
    app.include_router(groups_router, dependencies=[Depends(get_current_user)])
    app.include_router(ous_router, dependencies=[Depends(get_current_user)])
    app.include_router(containers_router, dependencies=[Depends(get_current_user)])

    return app


app = get_app()
