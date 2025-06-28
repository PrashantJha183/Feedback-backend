from pydantic import BaseModel, EmailStr
from typing import Literal


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["manager", "employee"]
    employee_id: str


class UserOut(BaseModel):
    name: str
    email: EmailStr
    role: Literal["manager", "employee"]
    employee_id: str


class UserLogin(BaseModel):
    employee_id: str
    password: str


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class PasswordReset(BaseModel):
    employee_id: str
    new_password: str
