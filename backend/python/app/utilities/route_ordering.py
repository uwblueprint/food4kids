"""Natural, case-insensitive ordering for route names.

Routes are generated as ``Route {n}``, so ordering by the name as text puts
``Route 10`` between ``Route 1`` and ``Route 2``. Names are editable, though,
so the ordering also has to place a renamed route sensibly: sorting on the
number alone would drop ``3rd shift`` between ``Route 2`` and ``Route 4``.

Names in practice are one text prefix followed by one number, so the key is
(text before the first digit, that number, the whole name): ``Cambridge`` sorts
among the text names, ``Route 1`` … ``Route 12`` count up inside their shared
prefix. Both text parts are lowered so ``route 1`` sits with ``Route 1``
rather than after ``Route 9``, and so the result doesn't depend on the
deployed database's collation. The raw name follows the lowered one, keeping
the order total when two names differ only in case.

This is the single source of truth for that ordering — the SQL form for
queries, the Python form for route lists already loaded in memory.
"""

import re
from typing import Any

from sqlalchemy import Integer, cast, func, nulls_last

# The name split in two: everything before the first digit, then that first run
# of digits. The run is capped at 9 digits so a name like "Route 9999999999999"
# cannot overflow the int cast in Postgres.
_TEXT_PREFIX = r"^[^0-9]*"
_NUMBER_RUN = r"\d{1,9}"


def route_name_order_by(name_col: Any, *tiebreak_cols: Any) -> list[Any]:
    """ORDER BY clauses sorting route names naturally, ignoring case.

    Splat into ``order_by``, after any leading keys (e.g. drive_date), passing
    a unique column as ``tiebreak_cols`` where the order has to be total.
    """
    return [
        func.lower(func.substring(name_col, _TEXT_PREFIX)),
        nulls_last(cast(func.substring(name_col, _NUMBER_RUN), Integer)),
        func.lower(name_col),
        name_col,
        *tiebreak_cols,
    ]


def route_name_sort_key(name: str) -> tuple[str, bool, int, str, str]:
    """``sorted`` key mirroring :func:`route_name_order_by`."""
    prefix = re.match(_TEXT_PREFIX, name)
    number = re.search(_NUMBER_RUN, name)
    return (
        prefix.group().lower() if prefix else "",
        number is None,
        int(number.group()) if number else 0,
        name.lower(),
        name,
    )
