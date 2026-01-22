from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class OUBase(BaseModel):
    ou: str = Field(..., description="OU Name")
    description: Optional[str] = Field(None, description="OU description")


class OUCreate(OUBase):
    parent_dn: str = Field(..., description="Parent DN")


class OUUpdate(BaseModel):
    description: Optional[str] = None
    parent_dn: Optional[str] = Field(
        None, description="DN родительского контейнера для перемещения"
    )


class OUResponse(OUBase):
    model_config = ConfigDict(from_attributes=True)

    dn: str = Field(..., description="Distinguished Name")
