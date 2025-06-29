from fastapi import APIRouter, HTTPException
from app.models.feedback import Feedback
from app.models.user import User
from app.models.feedback_request import FeedbackRequest
from app.models.notification import Notification
from app.schemas.feedback import (
    FeedbackCreate, FeedbackOut, CommentIn, ExportPDFResponse, FeedbackRequestIn
)
from datetime import datetime
from typing import List
import markdown2
import io
from reportlab.pdfgen import canvas
from fastapi.responses import StreamingResponse

router = APIRouter()

# Give Feedback (Manager)
@router.post("/", response_model=FeedbackOut)
async def give_feedback(feedback: FeedbackCreate):
    manager = await User.find_one(User.role == "manager")
    if not manager:
        raise HTTPException(403, "Only managers can give feedback")

    employee = await User.find_one(User.employee_id == feedback.employee_id)
    if not employee:
        raise HTTPException(404, "Employee not found")

    fb = Feedback(
        manager_id=manager.employee_id,
        employee_id=employee.employee_id,
        strengths=feedback.strengths,
        improvement=feedback.improvement,
        sentiment=feedback.sentiment,
        anonymous=feedback.anonymous or False,
        tags=feedback.tags or [],
        comments=[],
        acknowledged=False,
        created_at=datetime.utcnow()
    )
    await fb.insert()

    await Notification(
        employee_id=employee.employee_id,
        message="New feedback received"
    ).insert()

    return FeedbackOut.from_feedback(fb, manager.name)

# View Feedback History (Employee)
@router.get("/employee/{employee_id}", response_model=List[FeedbackOut])
async def get_feedback_history(employee_id: str):
    fbs = await Feedback.find(Feedback.employee_id == employee_id).to_list()
    out = []
    for fb in fbs:
        mgr = await User.find_one(User.employee_id == fb.manager_id)
        comments_html = [
            {"employee_id": c["employee_id"], "text": markdown2.markdown(c["text"])}
            for c in getattr(fb, "comments", [])
        ]
        out.append(FeedbackOut.from_feedback(fb, mgr.name if mgr else "Unknown", comments_html))
    return out

# Acknowledge Feedback
@router.patch("/acknowledge/{feedback_id}")
async def acknowledge(feedback_id: str):
    fb = await Feedback.get(feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback not found")
    fb.acknowledged = True
    await fb.save()
    return {"message": "Feedback acknowledged"}

# Update Feedback (Manager only)
@router.put("/{feedback_id}", response_model=FeedbackOut)
async def update_feedback(feedback_id: str, upd: FeedbackCreate):
    fb = await Feedback.get(feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback not found")

    mgr = await User.find_one(User.role == "manager")
    if not mgr or fb.manager_id != mgr.employee_id:
        raise HTTPException(403, "Not authorized")

    fb.strengths = upd.strengths
    fb.improvement = upd.improvement
    fb.sentiment = upd.sentiment
    fb.tags = upd.tags or []
    await fb.save()

    employee = await User.find_one(User.employee_id == fb.employee_id)
    return FeedbackOut.from_feedback(fb, mgr.name)

# Delete Feedback
@router.delete("/{feedback_id}")
async def delete_feedback(feedback_id: str):
    fb = await Feedback.get(feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback not found")

    mgr = await User.find_one(User.role == "manager")
    if fb.manager_id != mgr.employee_id:
        raise HTTPException(403, "Not authorized")

    await fb.delete()
    return {"message": "Deleted"}

# Delete All Feedback by Manager
@router.delete("/manager/{manager_id}")
async def delete_all(manager_id: str):
    mgr = await User.find_one(User.employee_id == manager_id, User.role == "manager")
    if not mgr:
        raise HTTPException(403, "Not authorized")

    deleted = await Feedback.find(Feedback.manager_id == manager_id).delete()
    return {"message": f"Deleted {deleted} items"}

# Employee Requests Feedback
@router.post("/request")
async def request_feedback(payload: FeedbackRequestIn):
    emp = await User.find_one(User.employee_id == payload.employee_id, User.role == "employee")
    if not emp:
        raise HTTPException(404, "Employee not found")
    
    fr = FeedbackRequest(employee_id=payload.employee_id, message=payload.message)
    await fr.insert()

    await Notification(
        user_id=payload.employee_id,
        message="You requested feedback. Await manager response."
    ).insert()

    return {"message": "Request submitted"}

# Add Comment to Feedback
@router.post("/comment/{feedback_id}")
async def comment(feedback_id: str, comment: CommentIn):
    fb = await Feedback.get(feedback_id)
    if not fb:
        raise HTTPException(404, "Feedback not found")

    emp = await User.find_one(User.employee_id == comment.employee_id)
    if not emp or emp.role != "employee":
        raise HTTPException(403, "Not authorized")

    fb.comments = getattr(fb, "comments", [])
    fb.comments.append({"employee_id": comment.employee_id, "text": comment.text})
    await fb.save()
    return {"message": "Comment added"}

# Export Feedback as PDF
@router.get("/export/{employee_id}", response_model=ExportPDFResponse)
async def export_pdf(employee_id: str):
    fbs = await Feedback.find(Feedback.employee_id == employee_id).to_list()
    buf = io.BytesIO()
    p = canvas.Canvas(buf)
    p.drawString(100, 800, f"Feedback Report for Employee ID: {employee_id}")
    y = 780
    for fb in fbs:
        p.drawString(100, y, f"{fb.sentiment.upper()} - {fb.strengths} | {fb.improvement}")
        y -= 20
        if y < 50:
            p.showPage()
            y = 800
    p.save()
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf")
