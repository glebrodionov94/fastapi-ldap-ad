import json
import os
from typing import Optional, Dict

from app.core.config import settings
from app.models.audit import AuditEvent


class AuditService:
    """
    Service for logging audit events to a file.
    This class provides functionality to log audit events, such as actions performed by users on resources, to a specified file in JSON lines format. It ensures the log directory exists and appends each event with a timestamp.
    Args:
      file_path (Optional[str]): Path to the audit log file. If not provided, uses the default from settings.
    Methods:
      log(actor, action, resource_type, resource_id, status, message, details):
        Logs an audit event with the specified details.
    """

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
        if hasattr(event, "timestamp") and hasattr(event.timestamp, "isoformat"):
            line["timestamp"] = event.timestamp.isoformat()
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


audit_service = AuditService()
