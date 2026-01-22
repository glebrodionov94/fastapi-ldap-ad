import json
import os
from typing import Optional, Dict

from app.core.config import settings
from app.models.audit import AuditEvent


class AuditService:
    def __init__(self, file_path: Optional[str] = None) -> None:
        self.file_path = file_path or settings.audit_log_path
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def log(
        self,
        *,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str,
        status: str = "success",
        message: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> None:
        event = AuditEvent(
            actor=actor,
            action=action,
            resource_type=resource_type,  # type: ignore[arg-type]
            resource_id=resource_id,
            status=status,  # type: ignore[arg-type]
            message=message,
            details=details,
        )
        line = event.model_dump()
        line["timestamp"] = event.timestamp.isoformat()
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


audit_service = AuditService()
