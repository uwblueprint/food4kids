import re

import phonenumbers


def validate_phone(v: str) -> str:
    try:
        parsed_phone = phonenumbers.parse(v, "CA")
        if not phonenumbers.is_valid_number(parsed_phone):
            raise ValueError("Invalid phone number")
        return phonenumbers.format_number(
            parsed_phone, phonenumbers.PhoneNumberFormat.E164
        )
    except phonenumbers.NumberParseException as e:
        raise ValueError("Invalid phone number format") from e


def validate_password_complexity(password: str) -> str:
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must contain at least one special character.")
    return password
