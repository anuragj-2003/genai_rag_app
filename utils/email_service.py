import smtplib
import random
import string
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_otp(length=6):
    """Generates a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(to_email, otp):
    """
    Sends an OTP email to the specified recipient.
    """
    sender_email = st.secrets["auth"].get("email_sender", "d.anuragj2003@gmail.com") # Default/Fallback
    password = st.secrets["auth"].get("email_password")
    
    if not password:
        return False, "Email password not configured in secrets."

    subject = "🔐 Verify your GenAI Workspace Account"
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px;">
                <h2 style="color: #4CAF50; text-align: center;">GenAI Workspace Verification</h2>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p>Hello,</p>
                <p>Thank you for signing up! Please use the following One-Time Password (OTP) to verify your email address and complete your registration.</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
                    <span style="font-size: 24px; font-weight: bold; letter-spacing: 5px; color: #333;">{otp}</span>
                </div>
                
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this, you can safely ignore this email.</p>
                
                <br>
                <p style="font-size: 12px; color: #888;">Best regards,<br>The GenAI Workspace Team</p>
            </div>
        </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)
