"""
Centralized config that lists all email types, their template files, and required fields, etc.
"""

EMAIL_TEMPLATES = {
                    "account-creation": {
                        "filename": "account-creation.html",
                        "default_subject": "Your Food4Kids Driver Account is Ready",
                        "required_context": ["Driver_Name_To_Replace", "Sign_Up_URL"]
                    },
                    "check-latest-announcement": { 
                        "filename": "check-latest-announcement.html",
                        "default_subject": "New Announcement",
                        "required_context": ["Driver_Name_To_Replace", "Announcement_Name", "Announcement_Body", "Announcement_URL"]
                    },
                    "reset-password": { 
                        "filename": "reset-password.html",
                        "default_subject": "Reset Your F4K Account Password!",
                        "required_context": ["Driver_Name_To_Replace", "Reset_Password_URL"]
                    },
                    "view-upcoming-route": { 
                        "filename": "view-upcoming-route.html",
                        "default_subject": "View Your Upcoming F4K Route",
                        "required_context": ["Driver_Name_To_Replace", "Date_To_Replace", "Time_To_Replace", "Route_Duration_To_Replace", "Upcoming_Route_URL"]
                    },
                }

def validate_email_context(email_type, context):
    """
    Checks if all required variables are present in the context dict. Raise ValueError if missing.
    """
    requiredVars = sorted(EMAIL_TEMPLATES[email_type]["required_context"])
    if requiredVars != sorted(context):
        raise ValueError("Missing one or more required fields of: "+ requiredVars)
    else:
        return

def get_email_template_config(email_type):
    return EMAIL_TEMPLATES[email_type]

