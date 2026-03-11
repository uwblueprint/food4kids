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
