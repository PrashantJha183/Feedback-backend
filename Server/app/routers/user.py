from fastapi import APIRouter, HTTPException
from app.models.user import User
from app.models.feedback import Feedback
from app.schemas.user import UserCreate, UserOut, UserLogin
from typing import List
from collections import Counter
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Register a new user (anyone allowed to register now)
@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate):
    existing = await User.find_one(User.employee_id == user.employee_id)
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")

    hashed_password = pwd_context.hash(user.password)
    new_user = User(**user.dict())
    new_user.password = hashed_password
    await new_user.insert()
    return UserOut(
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        employee_id=new_user.employee_id
    )

# Login route
@router.post("/login")
async def login_user(credentials: UserLogin):
    user = await User.find_one(User.employee_id == credentials.employee_id)
    if not user or not pwd_context.verify(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "message": "Login successful",
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "employee_id": user.employee_id
    }

# Manager: View all team members with feedback stats
@router.get("/dashboard/manager", response_model=List[dict])
async def manager_dashboard():
    employees = await User.find(User.role == "employee").to_list()
    result = []

    for emp in employees:
        feedbacks = await Feedback.find(Feedback.employee_id == emp.employee_id).to_list()
        sentiments = Counter([fb.sentiment for fb in feedbacks])
        result.append({
            "employee_id": emp.employee_id,
            "employee_name": emp.name,
            "feedback_count": len(feedbacks),
            "positive": sentiments.get("positive", 0),
            "neutral": sentiments.get("neutral", 0),
            "negative": sentiments.get("negative", 0)
        })

    return result

# Employee: View timeline of received feedback
@router.get("/dashboard/employee/{employee_id}", response_model=List[dict])
async def employee_dashboard(employee_id: str):
    user = await User.find_one(User.employee_id == employee_id)
    if not user or user.role != "employee":
        raise HTTPException(status_code=404, detail="Employee not found")

    feedbacks = await Feedback.find(Feedback.employee_id == employee_id).sort("-created_at").to_list()
    timeline = []
    for fb in feedbacks:
        manager = await User.find_one(User.employee_id == fb.manager_id)
        timeline.append({
            "feedback_id": str(fb.id),
            "manager_id": fb.manager_id,
            "manager_name": manager.name if manager else "Unknown",
            "strengths": fb.strengths,
            "improvement": fb.improvement,
            "sentiment": fb.sentiment,
            "acknowledged": fb.acknowledged,
            "created_at": fb.created_at
        })
    return timeline

# Update employee
@router.put("/{employee_id}", response_model=UserOut)
async def update_user(employee_id: str, updated_data: UserCreate):
    user = await User.find_one(User.employee_id == employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = pwd_context.hash(updated_data.password)
    user.name = updated_data.name
    user.email = updated_data.email
    user.password = hashed_password
    user.role = updated_data.role
    await user.save()

    return UserOut(
        name=user.name,
        email=user.email,
        role=user.role,
        employee_id=user.employee_id
    )

# Delete employee
@router.delete("/{employee_id}")
async def delete_user(employee_id: str):
    user = await User.find_one(User.employee_id == employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user.delete()
    return {"message": f"Employee {employee_id} deleted successfully"}
