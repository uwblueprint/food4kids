"""Free-text search predicates for the admin tables' search boxes.

Each list endpoint's ``?search=`` is a single box over several columns, so the
predicate is an OR across them rather than a per-field filter. Applied before
pagination so a page is drawn from the matches.
"""

import re
from typing import Any

from sqlalchemy import ColumnElement, SQLColumnExpression, String, cast, func, or_

_NON_DIGITS = re.compile(r"\D")
# What someone typing a phone number can type: digits and phone punctuation,
# nothing else. Anything with a letter in it is an address or a name.
_PHONE_QUERY = re.compile(r"^[\d\s()+.\-]+$")
# An area code's worth. Below this, a "phone" match is an accident of some
# other field's digits (a street number, a postal code's "T0T") and would
# match nearly every row.
_MIN_PHONE_DIGITS = 3


def text_match(term: str, *columns: SQLColumnExpression[Any]) -> ColumnElement[bool]:
    """Case-insensitive substring match of ``term`` against any of ``columns``."""
    pattern = f"%{term}%"
    return or_(*(column.ilike(pattern) for column in columns))


def phone_match(
    term: str, *columns: SQLColumnExpression[Any]
) -> ColumnElement[bool] | None:
    """Match ``term`` against ``columns`` comparing digits only.

    Phone numbers are stored RFC 3966 (``tel:+1-519-576-3443``) but read and
    typed in any of a dozen shapes, so a literal substring match on what
    someone types almost never lands. Returns None unless ``term`` reads as a
    phone number — digits and phone punctuation, at least an area code's worth
    — so the caller can leave phones out of the OR entirely.
    """
    if not _PHONE_QUERY.match(term):
        return None
    digits = _NON_DIGITS.sub("", term)
    if len(digits) < _MIN_PHONE_DIGITS:
        return None
    pattern = f"%{digits}%"
    return or_(
        *(
            func.regexp_replace(cast(column, String), r"\D", "", "g").like(pattern)
            for column in columns
        )
    )
