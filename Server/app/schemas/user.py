from pydantic import BaseModel, EmailStr
from typing import Literal

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["manager", "employee"]
    employee_id: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    employee_id: str

class UserLogin(BaseModel):
    employee_id: str
    password: str
