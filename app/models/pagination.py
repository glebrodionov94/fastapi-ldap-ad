from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "skip": 0,
                "limit": 10,
                "pages": 10,
            }
        }
    )

    items: list[T] = Field(..., description="Элементы текущей страницы")
    total: int = Field(..., description="Общее количество элементов")
    skip: int = Field(..., description="Количество пропущенных элементов")
    limit: int = Field(..., description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")
