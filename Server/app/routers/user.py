from fastapi import APIRouter, HTTPException
from app.models.user import User
from app.models.feedback import Feedback
from app.schemas.user import UserCreate, UserOut, UserLogin, PasswordUpdate, PasswordReset
from typing import List
from collections import Counter
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------------
# Register a new user (Manager only)
# -------------------------------
@router.post("/", response_model=UserOut)
async def create_user(
    user: UserCreate,
    manager_id: str = None
):
    """
    Only a manager can register a user.
    The manager_id must be provided and validated.
    """
    if not manager_id:
        raise HTTPException(status_code=403, detail="Manager authentication required")

    manager = await User.find_one(User.employee_id == manager_id)
    if not manager or manager.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can register users")

    existing = await User.find_one(User.employee_id == user.employee_id)
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")

    hashed_password = pwd_context.hash(user.password)

    new_user = User(**user.dict())
    new_user.password = hashed_password

    # assign the manager_employee_id if the user is an employee
    if new_user.role == "employee":
        new_user.manager_employee_id = manager_id
    else:
        new_user.manager_employee_id = None

    await new_user.insert()

    return UserOut(
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        employee_id=new_user.employee_id,
        manager_employee_id=new_user.manager_employee_id
    )


# -------------------------------
# User Login
# -------------------------------
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
        "employee_id": user.employee_id,
        "manager_employee_id": user.manager_employee_id
    }


# -------------------------------
# Manager Dashboard
# -------------------------------
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


# -------------------------------
# Employee Dashboard
# -------------------------------
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


# -------------------------------
# Fetch employees under a manager
# -------------------------------
@router.get("/manager/{manager_id}/employees", response_model=List[UserOut])
async def get_employees_under_manager(manager_id: str):
    # Check manager exists
    manager = await User.find_one(
        User.employee_id == manager_id, User.role == "manager"
    )
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    # Find all employees under this manager
    employees = await User.find(
        User.manager_employee_id == manager_id
    ).to_list()

    return [
        UserOut(
            name=emp.name,
            email=emp.email,
            role=emp.role,
            employee_id=emp.employee_id,
        )
        for emp in employees
    ]

# -------------------------------
# Update user (Manager only)
# -------------------------------
@router.put("/{employee_id}", response_model=UserOut)
async def update_user(employee_id: str, updated_data: UserCreate, manager_id: str = None):
    """
    Only managers can update user details.
    """
    if not manager_id:
        raise HTTPException(status_code=403, detail="Manager authentication required")

    manager = await User.find_one(User.employee_id == manager_id)
    if not manager or manager.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can update users")

    user = await User.find_one(User.employee_id == employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = pwd_context.hash(updated_data.password)
    user.name = updated_data.name
    user.email = updated_data.email
    user.password = hashed_password
    user.role = updated_data.role

    # update manager_employee_id if the user is an employee
    if user.role == "employee":
        user.manager_employee_id = manager_id
    else:
        user.manager_employee_id = None

    await user.save()

    return UserOut(
        name=user.name,
        email=user.email,
        role=user.role,
        employee_id=user.employee_id,
        manager_employee_id=user.manager_employee_id
    )


# -------------------------------
# Delete user (Manager only)
# -------------------------------
@router.delete("/{employee_id}")
async def delete_user(employee_id: str, manager_id: str = None):
    """
    Only managers can delete users.
    """
    if not manager_id:
        raise HTTPException(status_code=403, detail="Manager authentication required")

    manager = await User.find_one(User.employee_id == manager_id)
    if not manager or manager.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can delete users")

    user = await User.find_one(User.employee_id == employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user.delete()
    return {"message": f"Employee {employee_id} deleted successfully"}


# -------------------------------
# Change own password (User)
# -------------------------------
@router.put("/change-password/{employee_id}")
async def change_password(employee_id: str, data: PasswordUpdate):
    """
    User changes their own password. Requires old password.
    """
    user = await User.find_one(User.employee_id == employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(data.old_password, user.password):
        raise HTTPException(status_code=401, detail="Old password incorrect")

    hashed_new_password = pwd_context.hash(data.new_password)
    user.password = hashed_new_password
    await user.save()

    return {"message": "Password updated successfully"}


# -------------------------------
# Forgot password (User)
# -------------------------------
@router.post("/reset-password")
async def reset_password(data: PasswordReset):
    """
    Allows user to reset their password using employee ID and new password.
    """
    user = await User.find_one(User.employee_id == data.employee_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_new_password = pwd_context.hash(data.new_password)
    user.password = hashed_new_password
    await user.save()

    return {"message": "Password reset successfully. Please login with your new password."}
