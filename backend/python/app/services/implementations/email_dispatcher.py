"""
Used to send both event-driven and scheduled emails
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlmodel import select

from app.constants.email_config import (
    EMAIL_TEMPLATES,
    FOOTER_CONTEXT_KEYS,
    validate_email_context,
)


def _absolute_url(url: str | None) -> str:
    """Make a stored social link safe to put in an `href`.

    Nothing validates these on the way in -- the column is a plain string and
    the admin form never runs native validation -- so an admin can save
    `facebook.com/Food4KidsWR`. A mail client resolves that relative to
    nothing, giving a dead link: exactly what the `{% if %}` guards exist to
    avoid. Assume https when no scheme was typed.
    """
    if not url:
        return ""
    stripped = url.strip()
    if "://" in stripped:
        return stripped
    return f"https://{stripped}"


def _strip_scheme(url: str | None) -> str:
    """`https://food4kidswr.ca/` -> `food4kidswr.ca`, per the footer design."""
    if not url:
        return ""
    return url.removeprefix("https://").removeprefix("http://").rstrip("/")


if TYPE_CHECKING:
    import logging

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
        """Initialize email dispatcher"""
        self.email_service = email_service
        self.template_renderer = template_renderer
        self.logger = logger

    async def _org_contact_context(self) -> dict[str, str]:
        """The org's contact details, as the footer's template variables.

        Injected into every email rather than asked of callers: the footer is
        part of the shared layout, so requiring each call site to pass these
        would mean every future sender has to remember them, and forgetting
        would silently render an email with no footer.

        Read fresh every send, deliberately. ``get_email_dispatcher`` is
        ``@lru_cache``d, so there is exactly one dispatcher per process and any
        memoization here would last until restart -- an admin correcting the
        address in Settings would never see it take effect, and a single
        transient database fault would pin an empty footer forever. One
        single-row select is nothing next to the SMTP round trip it precedes.
        """
        from app.models import async_session_maker_instance
        from app.models.system_settings import SystemSettings

        blank = dict.fromkeys(FOOTER_CONTEXT_KEYS, "")

        if async_session_maker_instance is None:
            # No database wired up (unit tests constructing a dispatcher
            # directly). An email with an empty footer beats no email.
            self.logger.warning("No session maker; sending with an empty footer")
            return blank

        try:
            async with async_session_maker_instance() as session:
                result = await session.execute(select(SystemSettings).limit(1))
                settings = result.scalars().first()
        except Exception:
            # The footer is decorative; the email is not. Before this lookup
            # existed a settings problem could not fail a send, and it should
            # not start now -- log it and send without the footer.
            self.logger.exception("Could not read org contact; footer omitted")
            return blank

        if settings is None:
            self.logger.warning("No system settings row; sending with an empty footer")
            return blank

        return {
            # The design prints the bare domain, not the stored URL.
            "Org_Website": _strip_scheme(settings.f4k_wr_website),
            "Org_Address": settings.f4k_wr_address or "",
            # These land in an href, so they must be absolute.
            "Org_Facebook_URL": _absolute_url(settings.f4k_wr_facebook),
            "Org_Instagram_URL": _absolute_url(settings.f4k_wr_instagram),
            "Org_Twitter_URL": _absolute_url(settings.f4k_wr_twitter),
        }

    async def dispatch(
        self,
        email_type: str,
        to: str | list[str],
        context: dict[str, Any],
        subject: str | None = None,
    ) -> None:
        """Send email(s) from template with variable substitution.
        Works for both one-off and batch sends, treating single-recipient strings and lists uniformly.
        Attempts delivery to all recipients and collects per-recipient failures; if any sends
        fail, a RuntimeError summarizing failed recipients is raised after all attempts.
        Raises ValueError if email_type is unknown or required context is missing
        """
        # Validate email type and context
        validate_email_context(email_type, context)

        # Get template config from email config file
        template_config = EMAIL_TEMPLATES[email_type]
        template_name = template_config["filename"]

        # Use provided subject or template default (ensure non-None str)
        subject_str: str = (
            subject if subject is not None else template_config["default_subject"]
        )

        # The footer's values are ours, not the caller's, and must not be
        # overridden by a stray key of the same name.
        render_context = {**context, **(await self._org_contact_context())}

        # Render template with context
        try:
            html_body = self.template_renderer.render(template_name, render_context)
        except Exception as e:
            self.logger.error(
                f"Failed to render template for {email_type}: {e!s}",
                exc_info=True,
            )
            raise

        # Normalize recipients to concrete list
        recipients: list[str] = [to] if isinstance(to, str) else list(to)

        # Send to each recipient, collecting failures but attempting all deliveries
        failures: list[tuple[str, Exception]] = []
        for recipient_email in recipients:
            try:
                self.email_service.send_email(
                    to=recipient_email,
                    subject=subject_str,
                    body=html_body,
                )
                self.logger.info(f"Sent {email_type} email to {recipient_email}")
            except Exception as e:
                self.logger.error(
                    f"Failed to send {email_type} email to {recipient_email}: {e!s}",
                    exc_info=True,
                )
                failures.append((recipient_email, e))

        if failures:
            failed_addresses = [addr for addr, _ in failures]
            self.logger.error(
                f"Failed to send {email_type} email to {len(failures)} recipients: {failed_addresses}"
            )
            raise RuntimeError(
                f"Failed to send {email_type} email to {len(failures)} recipients: {failed_addresses}"
            )
