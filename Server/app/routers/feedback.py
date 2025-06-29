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


# NEW: Create feedback (manager giving feedback to employee)
@router.post("/", response_model=FeedbackOut)
async def create_feedback(payload: FeedbackCreate):
    mgr = await User.find_one(
        User.employee_id == payload.manager_id,
        User.role == "manager"
    )
    if not mgr:
        raise HTTPException(404, "Manager not found")

    employee = await User.find_one(
        User.employee_id == payload.employee_id,
        User.role == "employee"
    )
    if not employee:
        raise HTTPException(404, "Employee not found")

    fb = Feedback(
        employee_id=payload.employee_id,
        manager_id=payload.manager_id,
        strengths=payload.strengths,
        improvement=payload.improvement,
        sentiment=payload.sentiment,
        tags=payload.tags or [],
        acknowledged=False,
        comments=[],
        created_at=datetime.utcnow()
    )
    await fb.insert()

    # Optional: create notification for the employee
    await Notification(
        employee_id=payload.employee_id,
        message=f"You have received new feedback from manager {mgr.name}"
    ).insert()

    return FeedbackOut.from_feedback(fb, mgr.name)


# Employee Requests Feedback
@router.post("/request")
async def request_feedback(payload: FeedbackRequestIn):
    emp = await User.find_one(
        User.employee_id == payload.employee_id,
        User.role == "employee"
    )
    if not emp:
        raise HTTPException(404, "Employee not found")
    
    mgr = await User.find_one(
        User.employee_id == payload.manager_employee_id,
        User.role == "manager"
    )
    if not mgr:
        raise HTTPException(404, "Manager not found")

    fr = FeedbackRequest(
        employee_id=payload.employee_id,
        manager_employee_id=payload.manager_employee_id,
        message=payload.message,
        seen=False,
        created_at=datetime.utcnow()
    )
    await fr.insert()

    await Notification(
        employee_id=payload.manager_employee_id,
        message=f"Feedback request from employee {payload.employee_id}"
    ).insert()

    return {"message": "Feedback request submitted successfully"}


# NEW: Get all feedback requests for a manager
@router.get("/requests/{manager_id}")
async def get_feedback_requests(manager_id: str):
    mgr = await User.find_one(
        User.employee_id == manager_id,
        User.role == "manager"
    )
    if not mgr:
        raise HTTPException(404, "Manager not found")

    requests = await FeedbackRequest.find(
        FeedbackRequest.manager_employee_id == manager_id
    ).sort("-created_at").to_list()

    return [
        {
            "id": str(req.id),
            "employee_id": req.employee_id,
            "message": req.message,
            "seen": req.seen,
            "created_at": req.created_at
        }
        for req in requests
    ]


# NEW: Mark a feedback request as seen
@router.patch("/requests/{request_id}/seen")
async def mark_feedback_request_seen(request_id: str):
    req = await FeedbackRequest.get(request_id)
    if not req:
        raise HTTPException(404, "Feedback request not found")

    req.seen = True
    await req.save()
    return {"message": "Feedback request marked as seen"}


# NEW: Count unseen requests for manager
@router.get("/requests/{manager_id}/count-unseen")
async def count_unseen_requests(manager_id: str):
    mgr = await User.find_one(
        User.employee_id == manager_id,
        User.role == "manager"
    )
    if not mgr:
        raise HTTPException(404, "Manager not found")

    count = await FeedbackRequest.find(
        FeedbackRequest.manager_employee_id == manager_id,
        FeedbackRequest.seen == False
    ).count()

    return {"unseen_count": count}

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
    # Check that the employee exists and has role 'employee'
    emp = await User.find_one(
        User.employee_id == payload.employee_id,
        User.role == "employee"
    )
    if not emp:
        raise HTTPException(404, "Employee not found")
    
    # Check that the manager exists and has role 'manager'
    mgr = await User.find_one(
        User.employee_id == payload.manager_employee_id,
        User.role == "manager"
    )
    if not mgr:
        raise HTTPException(404, "Manager not found")

    # Save the feedback request
    fr = FeedbackRequest(
        employee_id=payload.employee_id,
        manager_employee_id=payload.manager_employee_id,
        message=payload.message
    )
    await fr.insert()

    # Create a notification for the manager
    await Notification(
        employee_id=payload.manager_employee_id,
        message=f"Feedback request from employee {payload.employee_id}"
    ).insert()

    return {"message": "Feedback request submitted successfully"}


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



# View Feedback History (Manager)
@router.get("/manager/{manager_id}", response_model=List[FeedbackOut])
async def get_manager_feedback_history(manager_id: str):
    # Check that the user is a manager
    mgr = await User.find_one(User.employee_id == manager_id, User.role == "manager")
    if not mgr:
        raise HTTPException(404, "Manager not found")

    # Find all feedback given by this manager
    fbs = await Feedback.find(Feedback.manager_id == manager_id).to_list()
    out = []
    for fb in fbs:
        employee = await User.find_one(User.employee_id == fb.employee_id)
        comments_html = [
            {"employee_id": c["employee_id"], "text": markdown2.markdown(c["text"])}
            for c in getattr(fb, "comments", [])
        ]
        out.append(
            FeedbackOut.from_feedback(
                fb,
                mgr.name,
                comments_html
            )
        )
    return out

