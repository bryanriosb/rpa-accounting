import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import logging

logger = logging.getLogger(__name__)

def send_email_with_attachments(recipients, subject, body, attachments_dir):
    """
    Sends an email with all files in a directory as attachments.
    """
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        logger.error("EMAIL_SENDER and EMAIL_PASSWORD environment variables must be set.")
        return

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    for root, _, files in os.walk(attachments_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {os.path.basename(filepath)}",
                    )
                    msg.attach(part)
                    logger.info(f"Attached file: {filepath}")
                except Exception as e:
                    logger.error(f"Could not attach file {filepath}: {e}")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipients, text)
        server.quit()
        logger.info("Email sent successfully!")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
