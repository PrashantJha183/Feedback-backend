from beanie import Document
from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional
from pydantic import ConfigDict

class User(Document):
    name: str
    email: EmailStr
    password: str
    role: Literal["manager", "employee"]
    employee_id: str
    manager_employee_id: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    class Settings:
        name = "users"  # Beanie collection name
