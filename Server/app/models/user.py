from beanie import Document
from pydantic import EmailStr
from typing import Literal
from pydantic import ConfigDict

class User(Document):
    name: str
    email: EmailStr
    password: str
    role: Literal["manager", "employee"]
    employee_id: str  

    model_config = ConfigDict(arbitrary_types_allowed=True)

    class Settings:
        name = "users"  #Beanie collection name
