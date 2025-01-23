# In email_sender.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import logging
import os
from dotenv import load_dotenv
import ssl

load_dotenv()


class EmailSender:
    def __init__(self):
        self.from_email = os.getenv("EMAIL_USER")
        self.from_password = os.getenv("EMAIL_PASS")

        if not self.from_email or not self.from_password:
            raise ValueError("EMAIL_USER and EMAIL_PASS must be set in the environment.")

    def send_email(self, to_emails, subject, html_message, attachments=None, from_email=None):
        """
        Send an email with optional attachments.

        attachments: A list of tuples like [('image1', image_bytes)] where 'image1' 
                     is the CID (Content-ID) and image_bytes are the binary content.
        """
        if not to_emails:
            logging.error("No recipient email addresses provided.")
            return

        logging.info(f"Attempting to send email to: {', '.join(to_emails)}")
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL(os.getenv("EMAIL_SERVER"), os.getenv("EMAIL_PORT"), context=context) as server:
                server.login(self.from_email, self.from_password)
                logging.info("SMTP server login successful.")

                for recipient in to_emails:
                    msg = MIMEMultipart('related')
                    msg["From"] = self.from_email if not from_email else from_email
                    msg["To"] = recipient
                    msg["Subject"] = subject

                    # Create alternative MIME part for HTML
                    alternative_part = MIMEMultipart('alternative')
                    msg.attach(alternative_part)

                    # HTML part
                    html_part = MIMEText(html_message, "html")
                    alternative_part.attach(html_part)

                    # Attach images or other attachments if provided
                    if attachments:
                        for cid, content in attachments:
                            image = MIMEImage(content)
                            image.add_header('Content-ID', f'<{cid}>')
                            msg.attach(image)

                    server.sendmail(self.from_email, recipient, msg.as_string())
                    logging.info(f"Email sent successfully to {recipient}")

        except smtplib.SMTPException as smtp_error:
            logging.error(f"SMTP error occurred: {smtp_error}")
        except Exception as e:
            logging.error(f"An error occurred while sending emails: {e}")
