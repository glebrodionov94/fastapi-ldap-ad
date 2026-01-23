from pydantic import BaseModel
from typing import Optional


class ContainerResponse(BaseModel):
    """Response model for container object."""

    dn: str
    cn: str
    description: Optional[str] = None


class ContainerCreate(BaseModel):
    """Request model for creating a container."""

    cn: str
    parent_dn: str
    description: Optional[str] = None


class ContainerUpdate(BaseModel):
    """Request model for updating container attributes."""

    description: Optional[str] = None
    parent_dn: Optional[str] = None
