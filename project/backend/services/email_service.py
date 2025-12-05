import smtplib #Python library for sending emails via SMTP
import json
from email.mime.text import MIMEText #For creating email body parts
from email.mime.multipart import MIMEMultipart #For combining multiple parts (HTML + plain text)

from config import SMTP_SERVER, SMTP_PORT, FRONTEND_URL, PASSWORD_RESET_EXPIRE_HOURS  # pylint: disable=import-error

#
#   This file defines functions to send emails using Gmail's SMTP server.
#

# Load email credentials from secrets.json
def load_email_credentials() -> tuple[str, str]:
    """Load SMTP credentials from secrets.json"""

    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    return secrets.get("SMTP_EMAIL", ""), secrets.get("SMTP_PASSWORD", "")


def send_email(to_email: str, 
               subject: str, 
               html_content: str, 
               text_content: str = None) -> bool:
    """ Send an email using Gmail SMTP."""

    smtp_email, smtp_password = load_email_credentials()
    
    if not smtp_email or not smtp_password:
        print("Error: SMTP credentials not configured in secrets.json")
        return False
    
    try:

        # Creates an email with multiple versions of the content
        # Email clients pick the best version they can display
        # The client prefers HTML over plain text if both are available
        msg = MIMEMultipart("alternative")
        
        
        msg["Subject"] = subject
        msg["From"] = f"tuevent <{smtp_email}>"
        msg["To"] = to_email
        
        # Add plain text version (fallback)
        if text_content:
            part1 = MIMEText(text_content, "plain")
            msg.attach(part1)
        
        # Add HTML version
        part2 = MIMEText(html_content, "html")
        msg.attach(part2)

        #
        #   At this point, by adding both "plain" and "html" the structure of the
        #   email is as follows:
        #
        #   Email Message (MIMEMultipart "alternative")
        #   ├── Part 1: Plain Text (fallback)
        #   │   "Hello, click here to reset: http://..."
        #   │
        #   └── Part 2: HTML (preferred)
        #       <html><body><h1>Password Reset</h1>...</body></html>
        
        # Connect to Gmail SMTP and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Enable TLS encryption
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send a password reset email with a reset link.
    """
    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    subject = "Reset Your Password - tuevent"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
            <h1 style="color: #1890ff; margin-bottom: 20px;">Password Reset Request</h1>
            
            <p>Hello,</p>
            
            <p>We received a request to reset your password for your tuevent account. Click the button below to reset your password:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" 
                   style="background-color: #1890ff; color: white; padding: 14px 28px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                    Reset Password
                </a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="background-color: #e9ecef; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 14px;">
                {reset_link}
            </p>
            
            <p><strong>This link will expire in {PASSWORD_RESET_EXPIRE_HOURS} hour(s).</strong></p>
            
            <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            
            <p style="color: #666; font-size: 12px;">
                This email was sent by tuevent. Please do not reply to this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    Hello,
    
    We received a request to reset your password for your tuevent account.
    
    Click the link below to reset your password:
    {reset_link}
    
    This link will expire in {PASSWORD_RESET_EXPIRE_HOURS} hour(s).
    
    If you didn't request a password reset, you can safely ignore this email.
    Your password will remain unchanged.
    
    - tuevent Team
    """
    
    return send_email(to_email, subject, html_content, text_content)
