"""
Centralized config that lists all email types, their template files, and required fields, etc.
"""

from typing import Any, TypedDict


class EmailTemplateConfig(TypedDict):
    filename: str
    default_subject: str
    required_context: list[str]


EMAIL_TEMPLATES: dict[str, EmailTemplateConfig] = {
    "account-creation": {
        "filename": "account-creation.html",
        "default_subject": "Your Food4Kids Driver Account is Ready",
        "required_context": [
            "Driver_Name_To_Replace",
            "Sign_Up_URL",
            "Hours_Till_Expiry",
        ],
    },
    "check-latest-announcement": {
        "filename": "check-latest-announcement.html",
        "default_subject": "New Announcement",
        "required_context": [
            "Driver_Name_To_Replace",
            "Announcement_Name",
            "Announcement_Body",
            "Announcement_URL",
        ],
    },
    "reset-password": {
        "filename": "reset-password.html",
        "default_subject": "Reset Your F4K Account Password!",
        "required_context": [
            "Driver_Name_To_Replace",
            "Reset_Password_URL",
            "Days_Till_Expiry",
        ],
    },
    "view-upcoming-route": {
        "filename": "view-upcoming-route.html",
        "default_subject": "View Your Upcoming F4K Route",
        "required_context": [
            "Driver_Name_To_Replace",
            "Date_To_Replace",
            "Time_To_Replace",
            "Route_Duration_To_Replace",
            "Upcoming_Route_URL",
        ],
    },
}


def validate_email_context(email_type: str, context: dict[str, Any]) -> None:
    """
    Checks if all required variables are present in the context dict. Raise ValueError if missing.
    """
    if email_type not in EMAIL_TEMPLATES:
        raise ValueError(f"Unknown email type: {email_type}")

    required_vars = set(EMAIL_TEMPLATES[email_type]["required_context"])
    provided_vars = set(context.keys())
    missing = sorted(required_vars - provided_vars)
    if missing:
        raise ValueError(f"Missing one or more required fields: {missing}")


def get_email_template_config(email_type: str) -> EmailTemplateConfig:
    if email_type not in EMAIL_TEMPLATES:
        raise ValueError(f"Unknown email type: {email_type}")
    return EMAIL_TEMPLATES[email_type]
