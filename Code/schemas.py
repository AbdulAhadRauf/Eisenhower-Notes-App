from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from models import UrgencyEnum, ImportanceEnum, TimeFrameEnum

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

# Task schemas
class TaskCreate(BaseModel):
    title: str
    description: str
    urgency: UrgencyEnum
    importance: ImportanceEnum
    time_frame: TimeFrameEnum

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[UrgencyEnum] = None
    importance: Optional[ImportanceEnum] = None
    time_frame: Optional[TimeFrameEnum] = None
    completed: Optional[bool] = None

class Task(BaseModel):
    id: int
    title: str
    description: str
    urgency: UrgencyEnum
    importance: ImportanceEnum
    time_frame: TimeFrameEnum
    user_id: int
    completed: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)

# User with tasks
class UserWithTasks(User):
    tasks: List[Task] = []
