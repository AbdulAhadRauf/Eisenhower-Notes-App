from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine, get_db
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
from typing import List
from scheduler import scheduler # Import the scheduler

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API with Authentication")

# --- Scheduler Startup and Shutdown Events ---
@app.on_event("startup")
def startup_event():
    """
    Start the scheduler when the application starts.
    """
    scheduler.start()
    print("Scheduler started...")

@app.on_event("shutdown")
def shutdown_event():
    """
    Gracefully shut down the scheduler when the application stops.
    """
    scheduler.shutdown()
    print("Scheduler shut down...")
# -------------------------------------------


# Authentication Routes

@app.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    db_user = db.query(UserDB).filter(UserDB.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = UserDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
def login_for_access_token(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
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
    """Get current user profile."""
    return current_user

# Task Routes (Protected)

@app.get("/")
def home():
    return {"message": "Welcome to the Task Manager API with Authentication"}

@app.post("/tasks/", response_model=Task)
def create_task(
    task: TaskCreate, 
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Create a new task for the authenticated user."""
    # Check if user already has a task with this title
    existing = db.query(TaskDB).filter(
        TaskDB.title == task.title,
        TaskDB.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="You already have a task with this title."
        )
    
    # Create new task
    new_task = TaskDB(**task.dict(), user_id=current_user.id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.get("/tasks/", response_model=List[Task])
def get_user_tasks(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
    completed: Optional[bool] = None
):
    """
    Get tasks for the authenticated user, 
    with optional filtering by completion status.
    """
    query = db.query(TaskDB).filter(TaskDB.user_id == current_user.id)
    if completed is not None:
        query = query.filter(TaskDB.completed == completed)
    return query.all()

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Get a specific task by ID for the authenticated user."""
    task = db.query(TaskDB).filter(
        TaskDB.id == task_id,
        TaskDB.user_id == current_user.id
    ).first()
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
    """Update a specific task for the authenticated user."""
    task = db.query(TaskDB).filter(
        TaskDB.id == task_id,
        TaskDB.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update only provided fields
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
    """Delete a specific task for the authenticated user."""
    task = db.query(TaskDB).filter(
        TaskDB.id == task_id,
        TaskDB.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return {"message": f"Task with ID {task_id} has been deleted"}


import uvicorn

if __name__ == "__main__":
    uvicorn.run(app)
