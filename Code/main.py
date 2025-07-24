import os
import shutil
from datetime import timedelta, datetime
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import TaskDB, UserDB
from schemas import (
    Task, TaskCreate, TaskUpdate, 
    User, UserCreate, UserLogin, Token
)
from typing import List, Optional

from auth import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from scheduler import scheduler

# Create the uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API with Authentication")

# --- Scheduler Startup and Shutdown Events ---
@app.on_event("startup")
def startup_event():
    try:
        scheduler.start()
        print("Scheduler started...")
    except Exception:
        print("Scheduler already running.")

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shut down...")

# --- Authentication Routes ---
@app.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = UserDB(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
def login_for_access_token(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=User)
def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

# --- Task Routes (Protected) ---
@app.post("/tasks/", response_model=Task)
def create_task(
    task: TaskCreate, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    query = db.query(TaskDB).filter(TaskDB.title.ilike(f"%{task.title}%")).first()
    if query:
        raise HTTPException(status_code=404, detail="Title already present, cannot add to database.")

    new_task = TaskDB(**task.dict(), user_id=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/tasks/", response_model=List[Task])
def get_user_tasks(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
    completed: Optional[bool] = None,
    urgency: Optional[str] = None,
    importance: Optional[str] = None,
    search_query: Optional[str] = None,):

    query = db.query(TaskDB).filter(TaskDB.user_id == current_user.id)
    if completed is not None:
        query = query.filter(TaskDB.completed == completed)
    
    if search_query:
        query = query.filter(TaskDB.title.ilike(f"%{search_query}%") | TaskDB.description.ilike(f"%{search_query}%"))
    if urgency:
        query = query.filter(TaskDB.urgency == urgency)
    if importance:
        query = query.filter(TaskDB.importance == importance)
    
    return query.all()

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Also delete associated files from the server
    task_upload_dir = os.path.join(UPLOAD_DIR, str(task.id))
    if os.path.exists(task_upload_dir):
        shutil.rmtree(task_upload_dir)

    db.delete(task)
    db.commit()
    return {"message": f"Task with ID {task_id} has been deleted"}

# --- File Upload/Download Routes ---
@app.post("/tasks/{task_id}/upload/{file_type}", response_model=Task)
async def upload_task_file(
    task_id: int,
    file_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if file_type not in ["image", "document", "voice"]:
        raise HTTPException(status_code=400, detail="Invalid file type specified.")

    # Create a specific directory for the task's uploads
    task_upload_dir = os.path.join(UPLOAD_DIR, str(task_id))
    os.makedirs(task_upload_dir, exist_ok=True)
    
    file_path = os.path.join(task_upload_dir, file.filename) # type: ignore

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update the task model with the file path
    if file_type == "image":
        task.image_path = file_path
    elif file_type == "document":
        task.document_path = file_path
    elif file_type == "voice":
        task.voice_note_path = file_path
    
    db.commit()
    db.refresh(task)
    
    return task

@app.get("/download/{task_id}/{filename}")
async def download_task_file(
    task_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    task = db.query(TaskDB).filter(TaskDB.id == task_id, TaskDB.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or you do not have permission.")

    file_path = os.path.join(UPLOAD_DIR, str(task_id), filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    # Check if the requested file actually belongs to the task
    is_valid_file = file_path in [task.image_path, task.document_path, task.voice_note_path]
    if not is_valid_file:
        raise HTTPException(status_code=403, detail="Access to this file is forbidden.")

    return FileResponse(path=file_path, filename=filename)
