import logging
from abc import ABC, abstractmethod
from typing import List

from triggers import Alert
from src.shared.email_sender import EmailSender

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Action(ABC):
    """
    Base class for all actions that can be taken when a trigger fires.
    """
    @abstractmethod
    def execute(self, alert: Alert) -> None:
        pass


class EmailAction(Action):
    """
    A simple email action using an EmailSender class.
    """

    def __init__(self, email_sender: EmailSender, recipients: List[str]):
        self.email_sender = email_sender
        self.recipients = recipients

    def execute(self, alert: Alert) -> None:
        subject = alert.title
        message = self._format_email_body(alert)
        logger.info(f"Sending alert via email: {subject} to {', '.join(self.recipients)}")
        self.email_sender.send_email(
            subject=subject,
            html_message=message,
            to_emails=self.recipients
        )

    def _format_email_body(self, alert: Alert) -> str:
        # Simple formatting. Modify as needed.
        details = "".join(
            f"<li><strong>{k}:</strong> {v}</li>"
            for k, v in alert.details.items()
        )
        html = f"""
        <html>
          <body>
            <h2>{alert.title}</h2>
            <p>{alert.message}</p>
            <ul>{details}</ul>
            <p><em>Timestamp: {alert.timestamp}</em></p>
          </body>
        </html>
        """
        return html
