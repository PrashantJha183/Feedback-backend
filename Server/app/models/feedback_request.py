from beanie import Document
from datetime import datetime

class FeedbackRequest(Document):
    employee_id: str
    message: str
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "feedback_requests"
