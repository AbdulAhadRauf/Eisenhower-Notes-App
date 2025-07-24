from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime
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
class TaskBase(BaseModel):
    title: str
    description: str
    urgency: UrgencyEnum
    importance: ImportanceEnum
    time_frame: TimeFrameEnum
    deadline: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[UrgencyEnum] = None
    importance: Optional[ImportanceEnum] = None
    time_frame: Optional[TimeFrameEnum] = None
    completed: Optional[bool] = None
    deadline: Optional[datetime] = None

class Task(TaskBase):
    id: int
    user_id: int
    completed: bool
    image_path: Optional[str] = None
    document_path: Optional[str] = None
    voice_note_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# User with tasks
class UserWithTasks(User):
    tasks: List[Task] = []
