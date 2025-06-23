from beanie import Document
from datetime import datetime
from pydantic import ConfigDict

class Notification(Document):
    employee_id: str
    message: str
    seen: bool = False
    created_at: datetime = datetime.utcnow()

    model_config = ConfigDict(arbitrary_types_allowed=True)

    class Settings:
        name = "notifications"
