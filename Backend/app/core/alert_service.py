import smtplib
from email.mime.text import MIMEText
from app.config import EMAIL_ADDRESS, EMAIL_PASSWORD, ALERT_RECEIVER

def send_email_alert(threat_level):
    try:
        msg = MIMEText(f"Unauthorized weapon detected. Threat level: {threat_level}")
        msg["Subject"] = "🚨 WDUP ALERT"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = ALERT_RECEIVER

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("Email alert sent.")
    except Exception as e:
        print("Email error:", e)