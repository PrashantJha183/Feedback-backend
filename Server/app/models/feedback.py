from beanie import Document
from typing import Literal, List, Dict
from datetime import datetime
from pydantic import ConfigDict

class Feedback(Document):
    manager_id: str
    employee_id: str
    strengths: str
    improvement: str
    sentiment: Literal["positive", "neutral", "negative"]
    anonymous: bool = False
    tags: List[str] = []
    comments: List[Dict[str, str]] = []
    created_at: datetime = datetime.utcnow()
    acknowledged: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)

    class Settings:
        name = "feedback"
