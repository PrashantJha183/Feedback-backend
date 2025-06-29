from beanie import Document
from datetime import datetime
from pydantic import ConfigDict
from typing import Optional

class Notification(Document):
    employee_id: str
    message: str
    manager_employee_id: Optional[str] = None
    manager_name: Optional[str] = None
    seen: bool = False
    created_at: datetime = datetime.utcnow()

    model_config = ConfigDict(arbitrary_types_allowed=True)

    class Settings:
        name = "notifications"
