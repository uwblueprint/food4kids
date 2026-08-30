"""Numeric-aware ordering for route names.

Routes are generated as ``Route {n}``, so ordering by the name as text puts
``Route 10`` between ``Route 1`` and ``Route 2``. Ordering by the first run of
digits in the name fixes that. Names are editable, so a name with no digits
sorts last and falls back to the name itself — never an error.

This is the single source of truth for that ordering: the SQL form for queries,
the Python form for route lists already loaded in memory.
"""

import re
from typing import Any

from sqlalchemy import Integer, cast, func, nulls_last

# First run of digits in the name, capped at 9 digits so a name like
# "Route 99999999999999" cannot overflow the int cast in Postgres.
_NUMBER_RUN = r"\d{1,9}"


def route_name_order_by(name_col: Any, *tiebreak_cols: Any) -> list[Any]:
    """ORDER BY clauses sorting route names by their number, then by name.

    Splat into ``order_by``, after any leading keys (e.g. drive_date), passing
    a unique column as ``tiebreak_cols`` where the order has to be total.
    """
    return [
        nulls_last(cast(func.substring(name_col, _NUMBER_RUN), Integer)),
        name_col,
        *tiebreak_cols,
    ]


def route_name_sort_key(name: str) -> tuple[bool, int, str]:
    """``sorted`` key mirroring :func:`route_name_order_by`."""
    match = re.search(_NUMBER_RUN, name)
    return (match is None, int(match.group()) if match else 0, name)
