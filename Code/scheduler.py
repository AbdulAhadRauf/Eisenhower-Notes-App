from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
from models import UserDB, TaskDB
from email_utils import send_email

def send_daily_reminders():
    """
    Fetches all users and their pending tasks, then sends email reminders.
    This function is designed to be run as a scheduled job.
    """
    print("Running daily task reminder job...")
    # Create a new database session for this job
    db: Session = SessionLocal()
    try:
        users = db.query(UserDB).all()
        for user in users:
            # We are fetching all tasks here, but you could add a filter 
            # for "pending" tasks if you add a status field to your TaskDB model.
            tasks = db.query(TaskDB).filter(TaskDB.user_id == user.id).all()
            
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
                    to_address=user.email,
                    subject="Your Daily Task Reminder",
                    body_html=email_body
                )
    finally:
        # Ensure the database session is closed
        db.close()

# Initialize the scheduler
scheduler = BackgroundScheduler()
# Schedule the job to run every day at a specific time (e.g., 8:00 AM)
# You can change the hour and minute to your preference.
scheduler.add_job(send_daily_reminders, 'cron', hour=8, minute=0)

