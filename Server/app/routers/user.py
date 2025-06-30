from fastapi import APIRouter, HTTPException, Query, Depends
from app.models.user import User
from app.models.feedback import Feedback
from app.schemas.user import (
    UserCreate,
    UserOut,
    UserLogin,
    PasswordUpdate,
    PasswordReset,
    UserUpdate,  # Keep as is
)
from typing import List
from collections import Counter
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------------
# Register a user
# -------------------------------
@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate):
    existing = await User.find_one(User.employee_id == user.employee_id)
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists.")

    if user.role == "employee":
        if not user.manager_employee_id:
            raise HTTPException(
                status_code=400, detail="manager_employee_id required for employees."
            )

        manager = await User.find_one(User.employee_id == user.manager_employee_id)
        if not manager or manager.role != "manager":
            raise HTTPException(status_code=404, detail="Manager not found.")

    hashed_password = pwd_context.hash(user.password)

    new_user = User(**user.dict())
    new_user.password = hashed_password
    await new_user.insert()

    return UserOut(
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        employee_id=new_user.employee_id,
        manager_employee_id=new_user.manager_employee_id,
    )


# -------------------------------
# User Login
# -------------------------------
@router.post("/login")
async def login_user(credentials: UserLogin):
    user = await User.find_one(User.employee_id == credentials.employee_id)
    if not user or not pwd_context.verify(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    return {
        "message": "Login successful.",
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "employee_id": user.employee_id,
        "manager_employee_id": user.manager_employee_id,
    }


# -------------------------------
# Manager Dashboard
# -------------------------------
@router.get("/dashboard/manager/{manager_id}", response_model=List[dict])
async def manager_dashboard(manager_id: str):
    manager = await User.find_one(User.employee_id == manager_id)
    if not manager or manager.role != "manager":
        raise HTTPException(status_code=404, detail="Manager not found.")

    employees = await User.find(User.manager_employee_id == manager_id).to_list()

    result = []
    for emp in employees:
        feedbacks = await Feedback.find(
            Feedback.employee_id == emp.employee_id
        ).to_list()

        sentiments = Counter([fb.sentiment for fb in feedbacks])

        result.append(
            {
                "employee_id": emp.employee_id,
                "employee_name": emp.name,
                "feedback_count": len(feedbacks),
                "positive": sentiments.get("positive", 0),
                "neutral": sentiments.get("neutral", 0),
                "negative": sentiments.get("negative", 0),
            }
        )

    return result


# -------------------------------
# Employee Dashboard
# -------------------------------
@router.get("/dashboard/employee/{employee_id}", response_model=List[dict])
async def employee_dashboard(employee_id: str):
    user = await User.find_one(User.employee_id == employee_id)
    if not user or user.role != "employee":
        raise HTTPException(status_code=404, detail="Employee not found.")

    feedbacks = (
        await Feedback.find(Feedback.employee_id == employee_id)
        .sort("-created_at")
        .to_list()
    )

    timeline = []
    for fb in feedbacks:
        manager = await User.find_one(User.employee_id == fb.manager_employee_id)
        timeline.append(
            {
                "feedback_id": str(fb.id),
                "manager_id": fb.manager_employee_id,
                "manager_name": manager.name if manager else "Unknown",
                "strengths": fb.strengths,
                "improvement": fb.improvement,
                "sentiment": fb.sentiment,
                "acknowledged": fb.acknowledged,
                "created_at": fb.created_at,
            }
        )

    return timeline


# -------------------------------
# Get employees under a manager
# -------------------------------
@router.get("/manager/{manager_id}/employees", response_model=List[UserOut])
async def get_employees_under_manager(manager_id: str):
    manager = await User.find_one(User.employee_id == manager_id)
    if not manager or manager.role != "manager":
        raise HTTPException(status_code=404, detail="Manager not found.")

    employees = await User.find(User.manager_employee_id == manager_id).to_list()

    return [
        UserOut(
            name=emp.name,
            email=emp.email,
            role=emp.role,
            employee_id=emp.employee_id,
            manager_employee_id=emp.manager_employee_id,
        )
        for emp in employees
    ]


# -------------------------------
# Delete employee - Manager Only
# -------------------------------
@router.delete("/{manager_id}/{employee_id}")
async def delete_employee(manager_id: str, employee_id: str):
    manager = await User.find_one(User.employee_id == manager_id)
    if not manager or manager.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can delete employees.")

    employee = await User.find_one(User.employee_id == employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    if employee.manager_employee_id != manager_id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete employees under your management.",
        )

    await employee.delete()
    return {"message": f"Employee {employee_id} deleted successfully."}


# -------------------------------
# Update employee - Manager Only
# -------------------------------
@router.put("/{manager_id}/{employee_id}")
async def update_employee(manager_id: str, employee_id: str, update_data: UserUpdate):
    manager = await User.find_one(User.employee_id == manager_id)
    if not manager or manager.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can update employees.")

    employee = await User.find_one(User.employee_id == employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    if employee.manager_employee_id != manager_id:
        raise HTTPException(
            status_code=403,
            detail="You can only update employees under your management.",
        )

    updates = update_data.dict(exclude_unset=True)

    if "password" in updates and updates["password"]:
        updates["password"] = pwd_context.hash(updates["password"])
    elif "password" in updates and not updates["password"]:
        updates.pop("password")

    await employee.set(updates)

    return {"message": f"Employee {employee_id} updated successfully."}


# -------------------------------
# Change Password (Old + New)
# -------------------------------
@router.patch("/change-password/{employee_id}")
async def change_password(employee_id: str, data: PasswordUpdate):
    user = await User.find_one(User.employee_id == employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if not pwd_context.verify(data.old_password, user.password):
        raise HTTPException(status_code=401, detail="Old password is incorrect.")

    new_hashed = pwd_context.hash(data.new_password)
    await user.set({"password": new_hashed})

    return {"message": "Password updated successfully."}


# -------------------------------
# Forgot Password
# -------------------------------
@router.patch("/forgot-password/{employee_id}")
async def forgot_password(employee_id: str, data: PasswordReset):
    user = await User.find_one(User.employee_id == employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_hashed = pwd_context.hash(data.new_password)
    await user.set({"password": new_hashed})

    return {"message": "Password reset successfully."}
