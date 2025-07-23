import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# Fetch Gmail credentials from environment variables
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_email(to_address: str, subject: str, body_html: str):
    """
    Sends an email using Gmail's SMTP server.

    Args:
        to_address (str): The recipient's email address.
        subject (str): The subject of the email.
        body_html (str): The HTML content of the email body.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("Error: GMAIL_USER or GMAIL_APP_PASSWORD environment variables not set.")
        return

    # Create the email message
    msg = MIMEMultipart('alternative')
    msg['From'] = GMAIL_USER
    msg['To'] = to_address
    msg['Subject'] = subject

    # Attach the HTML body
    msg.attach(MIMEText(body_html, 'html'))

    try:
        # Connect to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        # Login to the account
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        # Send the email
        server.sendmail(GMAIL_USER, to_address, msg.as_string())
        # Close the connection
        server.quit()
        print(f"Successfully sent email to {to_address}")
    except Exception as e:
        print(f"Failed to send email to {to_address}. Error: {e}")

