from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.security import JWTHandler
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest) -> TokenResponse:
    """
    Получить JWT токен.

    Используется для получения токена доступа.
    В реальном приложении здесь должна быть проверка против LDAP/AD.
    """
    # Проверка тестовых учётных данных
    # В реальном приложении: ldap_service.authenticate(username, password)
    if not credentials.username or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Создание токена с пользовательскими данными
    token_data = {"sub": credentials.username, "username": credentials.username}
    access_token = JWTHandler.create_token(token_data)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_hours * 3600,
    )


@router.post("/refresh")
def refresh_token(current_user: dict = None) -> TokenResponse:
    """Обновить JWT токен."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    token_data = {
        "sub": current_user.get("username"),
        "username": current_user.get("username"),
    }
    access_token = JWTHandler.create_token(token_data)

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_expiration_hours * 3600,
    )
