from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["manager", "employee"]
    employee_id: str
    manager_employee_id: Optional[str] = None
    """
    Required if creating an employee.
    Managers should leave it as None.
    """

class UserOut(BaseModel):
    name: str
    email: EmailStr
    role: Literal["manager", "employee"]
    employee_id: str
    manager_employee_id: Optional[str] = None

class UserLogin(BaseModel):
    employee_id: str
    password: str

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

class PasswordReset(BaseModel):
    employee_id: str
    new_password: str

# -----------------------------
# NEW: Add this for updates
# -----------------------------
class UserUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    role: Optional[Literal["manager", "employee"]]
    manager_employee_id: Optional[str]
