from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class GroupBase(BaseModel):
    cn: str = Field(..., description="Group Common Name")
    description: Optional[str] = Field(None, description="Group description")


class GroupCreate(GroupBase):
    ou: str = Field(..., description="Organizational Unit DN")
    groupType: int = Field(
        default=-2147483646, description="Group type (default: Global Security)"
    )


class GroupUpdate(BaseModel):
    description: Optional[str] = None
    parent_dn: Optional[str] = Field(
        None, description="DN родительского контейнера для перемещения"
    )


class GroupResponse(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    dn: str = Field(..., description="Distinguished Name")
    member: Optional[list[str]] = Field(default=[], description="Group members DNs")
