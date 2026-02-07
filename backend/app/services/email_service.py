from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List

from backend.app.core.config import settings


conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
)


class EmailService:
    def __init__(self):
        self.fastmail = FastMail(conf)

    async def send_reset_password_email(self, email_to: str, token: str) -> None:
        """Send password reset email with token link."""
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4F46E5;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password for your Finance Tracker account.</p>
                <p>Click the button below to reset your password:</p>
                <a href="{reset_link}" class="button">Reset Password</a>
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #4F46E5;">{reset_link}</p>
                <p><strong>This link will expire in 15 minutes.</strong></p>
                <div class="footer">
                    <p>If you didn't request this, please ignore this email.</p>
                    <p>— Finance Tracker Team</p>
                </div>
            </div>
        </body>
        </html>
        """

        message = MessageSchema(
            subject="Reset Your Password - Finance Tracker",
            recipients=[email_to],
            body=html_content,
            subtype=MessageType.html,
        )

        await self.fastmail.send_message(message)


email_service = EmailService()
