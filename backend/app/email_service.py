import smtplib
from email.mime.text import MIMEText
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, INVITE_FROM


def send_invite_email(to_email: str, invite_link: str, role: str, studio_id: int):
    subject = "You’ve been invited"
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h2>You’ve been invited</h2>
        <p>You have been invited to join studio <b>{studio_id}</b> as <b>{role}</b>.</p>
        <p>Click below to accept the invite and create your account:</p>
        <p><a href="{invite_link}">{invite_link}</a></p>
        <p>This link expires in 24 hours.</p>
      </body>
    </html>
    """

    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = INVITE_FROM
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(INVITE_FROM, [to_email], msg.as_string())