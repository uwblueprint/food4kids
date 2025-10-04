from abc import ABC, abstractmethod
from typing import Any


class IEmailService(ABC):
    """
    EmailService interface for handling email related functionality
    """

    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        """
        Sends email with given parameters

        :param to: recipient's email
        :type to: str
        :param subject: email subject
        :type subject: str
        :param body: email body as html
        :type body: str
        :return: a dict that contains fields like id, threadId, labelIds
        of the sent email
        :rtype: dict
        :raises Exception: if email was not sent successfully
        """
        pass
