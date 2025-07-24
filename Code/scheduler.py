from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
from models import UserDB, TaskDB
from email_utils import send_email

def send_daily_reminders():
    """
    Fetches all users and their PENDING tasks, then sends email reminders.
    This function is designed to be run as a scheduled job.
    """
    print("Running daily task reminder job...")
    db: Session = SessionLocal()
    try:
        users = db.query(UserDB).all()
        for user in users:
            # Fetch only incomplete tasks for the reminder
            tasks = db.query(TaskDB).filter(
                TaskDB.user_id == user.id,
                TaskDB.completed == False  # <-- IMPROVEMENT: Only fetch pending tasks
            ).all()
            
            if tasks:
                # Compose the HTML for the email body
                task_list_html = "".join([f"<li><b>{task.title}:</b> {task.description}</li>" for task in tasks])
                email_body = f"""
                <html>
                <body>
                    <h2>Hi {user.username},</h2>
                    <p>Here are your pending tasks for today:</p>
                    <ul>
                        {task_list_html}
                    </ul>
                    <p>Have a productive day!</p>
                </body>
                </html>
                """
                
                # Send the email
                send_email(
                    to_address=user.email, # type: ignore
                    subject="Your Daily Task Reminder",
                    body_html=email_body
                )
    finally:
        # Ensure the database session is closed
        db.close()

# Initialize the scheduler
scheduler = BackgroundScheduler()
# Schedule the job to run every day at 8:00 AM
scheduler.add_job(send_daily_reminders, 'cron', hour=11, minute=0)
scheduler.add_job(send_daily_reminders, 'cron', hour=14, minute=30)
