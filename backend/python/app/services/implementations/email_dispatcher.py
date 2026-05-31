"""
Used to send both event-driven and scheduled emails
"""

from __future__ import annotations

import logging
from typing import Any

from app.constants.email_config import EMAIL_TEMPLATES, validate_email_context
from app.services.implementations.email_service import EmailService
from app.templates.email_renderer import TemplateRenderer


class EmailDispatcher:
    """Unified dispatcher for sending emails from templates with variable substitution.
    
    Handles both event-driven (e.g., user signup) and scheduled (e.g., cron) emails.
    Renders templates using Jinja2 and sends via EmailService.
    """

    def __init__(
        self,
        email_service: EmailService,
        template_renderer: TemplateRenderer,
        logger: logging.Logger,
    ):
        """Initialize email dispatcher
        """
        self.email_service = email_service
        self.template_renderer = template_renderer
        self.logger = logger

    async def dispatch(
        self,
        email_type: str,
        to: str | list[str],
        context: dict[str, Any],
        subject: str | None = None,
    ) -> None:
        """Send email(s) from template with variable substitution.
            Works for both one-off and batch sends, treating single-recipient strings and lists uniformly.
            Raises ValueError if email_type is unknown or required context is missing
        """
        # Validate email type and context
        validate_email_context(email_type, context)
        
        # Get template config from email config file
        template_config = EMAIL_TEMPLATES[email_type]
        template_name = template_config["filename"]
        
        # Use provided subject or template default
        if subject is None:
            subject = template_config["default_subject"]
        
        # Render template with context
        try:
            html_body = self.template_renderer.render(template_name, context)
        except Exception as e:
            self.logger.error(
                f"Failed to render template for {email_type}: {e!s}",
                exc_info=True,
            )
            raise
        
        # Normalize recipients to list
        recipients = [to] if isinstance(to, str) else to
        
        # Send to each recipient
        for recipient_email in recipients:
            try:
                self.email_service.send_email(
                    to=recipient_email,
                    subject=subject,
                    body=html_body,
                )
                self.logger.info(
                    f"Sent {email_type} email to {recipient_email}"
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to send {email_type} email to {recipient_email}: {e!s}",
                    exc_info=True,
                )
                raise
