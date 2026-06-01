"""
email_service.py — SMTP email delivery for OTP codes.
Uses smtplib (stdlib) with TLS. No external library needed.
"""

import smtplib
import secrets
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def generate_otp() -> str:
    """Generate a 6-digit OTP (cryptographically random)."""
    return str(secrets.randbelow(1_000_000)).zfill(6)


def send_otp_email(to_email: str, otp: str, purpose: str = "verification"):
    """
    Send OTP via SMTP with TLS.
    Raises smtplib.SMTPException on delivery failure.
    """
    subject_map = {
        "verification": "Your GenAI RAG Verification Code",
        "reset": "Your GenAI RAG Password Reset Code",
    }
    subject = subject_map.get(purpose, "Your Verification Code")

    html_body = f"""
    <html><body style="font-family:sans-serif;max-width:480px;margin:auto;padding:24px">
      <h2 style="color:#6366f1">GenAI RAG App</h2>
      <p>Your {purpose} code is:</p>
      <div style="font-size:36px;font-weight:bold;letter-spacing:8px;
                  background:#f1f5f9;padding:16px;border-radius:8px;
                  text-align:center;color:#1e293b">{otp}</div>
      <p style="color:#64748b;font-size:13px;margin-top:16px">
        This code expires in <strong>10 minutes</strong>.<br>
        Never share this code with anyone.
      </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
    except Exception as e:
        print(f"[Email] Failed to send OTP to {to_email}: {e}")
        raise
