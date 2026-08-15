import re

import phonenumbers


def validate_phone(v: str) -> str:
    """Normalize a phone number to RFC 3966 (``tel:+1-519-576-3443;ext=1``).

    RFC 3966 rather than E.164 because E.164 has no extension field: it parses
    ``(519) 576-3443 Ext. 1`` happily and then drops the ``Ext. 1`` on the way
    out. F4K's own contact number has an extension, and school delivery
    locations routinely do, so silently truncating to the switchboard sends a
    driver to the wrong line with nothing raised. The stored value doubles as
    the ``tel:`` URI a call button needs.
    """
    try:
        parsed_phone = phonenumbers.parse(v, "CA")
        if not phonenumbers.is_valid_number(parsed_phone):
            raise ValueError("Invalid phone number")
        return phonenumbers.format_number(
            parsed_phone, phonenumbers.PhoneNumberFormat.RFC3966
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
