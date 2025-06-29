from beanie import Document
from datetime import datetime

class FeedbackRequest(Document):
    employee_id: str
    manager_employee_id: str
    message: str
    seen: bool = False
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "feedback_requests"
