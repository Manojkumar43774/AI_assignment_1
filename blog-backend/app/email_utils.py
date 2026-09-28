import smtplib
from email.mime.text import MIMEText

from fastapi import HTTPException

from .config import settings


def send_otp_email(to_email: str, otp: str) -> None:
    if not settings.smtp_username or not settings.smtp_password:
        raise HTTPException(
            status_code=503,
            detail="Email sending is not configured. Set SMTP_USERNAME and SMTP_PASSWORD in backend/.env",
        )

    from_address = settings.smtp_from_address or settings.smtp_username

    message = MIMEText(
        f"Your Chronicles verification code is {otp}. It expires in "
        f"{settings.otp_expire_minutes} minutes."
    )
    message["Subject"] = "Your Chronicles verification code"
    message["From"] = from_address
    message["To"] = to_email

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(from_address, [to_email], message.as_string())
    except smtplib.SMTPException as exc:
        raise HTTPException(status_code=502, detail="Failed to send verification email") from exc
