import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import (
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    ALERT_RECEIVER
)


def send_email_alert(threat_level, detections=None):

    try:

        weapon_count = len([
            d for d in (detections or [])
            if d["class"] in ["Gun", "Weapon"]
        ])

        person_count = len([
            d for d in (detections or [])
            if d["class"] == "Person"
        ])

        html = f"""
        <html>
        <body>
            <h2 style="color:red;">
                Security Threat Detected
            </h2>

            <p>
                An unauthorized weapon carrier has been detected
                by the WDUP Surveillance System.
            </p>

            <table border="1" cellpadding="8">
                <tr>
                    <td><b>Threat Level</b></td>
                    <td>{threat_level}</td>
                </tr>
                <tr>
                    <td><b>Weapons Detected</b></td>
                    <td>{weapon_count}</td>
                </tr>
                <tr>
                    <td><b>Persons Detected</b></td>
                    <td>{person_count}</td>
                </tr>
            </table>

            <br>

            <p>
                Immediate verification and response is recommended.
            </p>

            <hr>

            <small>
                WDUP - Weapon Detection in Unauthorized Persons
                <br>
                Automated Security Notification
            </small>

        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")

        msg["Subject"] = "[WDUP ALERT] Unauthorized Weapon Detection"
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = ALERT_RECEIVER

        msg.attach(MIMEText(html, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.send_message(msg)

        server.quit()

        print("Alert email sent successfully.")

    except Exception as e:
        print("Email error:", e)