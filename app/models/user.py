from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserBase(BaseModel):
    cn: str = Field(..., description="Common Name")
    sAMAccountName: str = Field(..., description="Username")
    givenName: Optional[str] = Field(None, description="First Name")
    sn: Optional[str] = Field(None, description="Last Name")
    mail: Optional[str] = Field(None, description="Email")
    telephoneNumber: Optional[str] = Field(None, description="Phone")
    title: Optional[str] = Field(None, description="Job Title")
    department: Optional[str] = Field(None, description="Department")
    description: Optional[str] = Field(None, description="Description")


class UserCreate(UserBase):
    password: str = Field(..., description="User password")
    ou: str = Field(..., description="Organizational Unit DN")


class UserUpdate(BaseModel):
    givenName: Optional[str] = None
    sn: Optional[str] = None
    mail: Optional[str] = None
    telephoneNumber: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    password: Optional[str] = Field(
        None, min_length=8, description="Новый пароль (мин 8 символов)"
    )
    parent_dn: Optional[str] = Field(
        None, description="DN родительского контейнера для перемещения"
    )


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    dn: str = Field(..., description="Distinguished Name")
    userAccountControl: Optional[int] = None
    memberOf: list[str] = Field(
        default_factory=list, description="Группы, в которых состоит пользователь"
    )
