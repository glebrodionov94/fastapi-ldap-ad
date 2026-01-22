from datetime import datetime
from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str
    action: str
    resource_type: Literal["user", "group", "ou", "system"]
    resource_id: str
    status: Literal["success", "failure"]
    message: Optional[str] = None
    details: Optional[Dict] = None
