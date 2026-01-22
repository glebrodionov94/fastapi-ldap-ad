from datetime import datetime, timedelta
from typing import Dict, Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.core.config import settings


class JWTHandler:
    """JWT token handler for authentication."""

    @staticmethod
    def create_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT token with given data."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + settings.get_jwt_expiration()

        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )


security = HTTPBearer()


async def get_current_user(credentials=Depends(security)) -> Dict:
    """Dependency to get current user from JWT token."""
    token = credentials.credentials
    payload = JWTHandler.verify_token(token)
    return payload
