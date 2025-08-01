from sqlalchemy import Boolean, Column, Integer, String, Enum as SqlEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import enum

class UrgencyEnum(str, enum.Enum):
    urgent = "urgent"
    not_urgent = "not_urgent"

class ImportanceEnum(str, enum.Enum):
    important = "important"
    not_important = "not_important"

class TimeFrameEnum(str, enum.Enum):
    long_term = "long_term"
    short_term = "short_term"

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    tasks = relationship("TaskDB", back_populates="owner")

class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    urgency = Column(SqlEnum(UrgencyEnum))
    importance = Column(SqlEnum(ImportanceEnum))
    time_frame = Column(SqlEnum(TimeFrameEnum))
    completed = Column(Boolean, default=False, nullable=False)
    
    # New fields
    deadline = Column(DateTime, nullable=True)
    image_path = Column(String, nullable=True)
    document_path = Column(String, nullable=True)
    voice_note_path = Column(String, nullable=True)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("UserDB", back_populates="tasks")
