from pydantic import BaseModel
from typing import Literal, List, Optional
from datetime import datetime

class FeedbackCreate(BaseModel):
    manager_employee_id: str
    employee_id: str
    strengths: str
    improvement: str
    sentiment: str
    anonymous: Optional[bool] = False
    tags: Optional[List[str]] = []


class CommentIn(BaseModel):
    employee_id: str
    text: str


class FeedbackRequestIn(BaseModel):
    employee_id: str
    manager_employee_id: str
    message: str

class FeedbackOut(BaseModel):
    id: str
    manager_id: str
    manager_name: str
    employee_id: str
    strengths: str
    improvement: str
    sentiment: str
    anonymous: bool
    tags: List[str]
    comments: List[dict]
    acknowledged: bool
    created_at: datetime

    @classmethod
    def from_feedback(cls, fb, manager_name, comments_html=None):
        return cls(
            id=str(fb.id),
            manager_id=fb.manager_id,
            manager_name=manager_name,
            employee_id=fb.employee_id,
            strengths=fb.strengths,
            improvement=fb.improvement,
            sentiment=fb.sentiment,
            anonymous=fb.anonymous,
            tags=fb.tags,
            comments=comments_html if comments_html is not None else fb.comments,
            acknowledged=fb.acknowledged,
            created_at=fb.created_at
        )

class ExportPDFResponse(BaseModel):
    pass  # handled via StreamingResponse
