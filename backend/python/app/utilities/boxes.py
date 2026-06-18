"""Box-count derivation.

A location's box count is not stored; it is derived from the number of
children served there and the global ``children_per_box`` system setting:

    boxes = ceil(num_children / children_per_box)

This is the single source of truth for that formula. Callers must supply the
configured ``children_per_box`` (read from system settings) rather than
hardcoding a divisor.
"""

import math
from typing import TYPE_CHECKING, Any

from sqlalchemy import Integer, cast, func

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Fallback when system settings haven't been configured (matches the
# SystemSettings.children_per_box model default). Read paths that aggregate
# box counts use this rather than failing when no settings row exists yet.
DEFAULT_CHILDREN_PER_BOX = 2


def compute_boxes(num_children: int, children_per_box: int) -> int:
    """Boxes needed for ``num_children`` recipients at ``children_per_box`` each.

    Raises:
        ValueError: if ``children_per_box`` is not a positive integer, or
            ``num_children`` is negative — both indicate a misconfiguration we
            want to surface rather than silently coerce.
    """
    if children_per_box < 1:
        raise ValueError(
            f"children_per_box must be >= 1 to derive a box count, got {children_per_box}"
        )
    if num_children < 0:
        raise ValueError(f"num_children must be >= 0, got {num_children}")
    return math.ceil(num_children / children_per_box)


def box_count_expr(num_children: Any, children_per_box: int) -> Any:
    """SQL expression mirroring ``compute_boxes`` for use inside queries.

    Produces ``ceil(num_children / children_per_box)`` as an integer, so box
    totals can be summed in the database (e.g. per route / route group).
    ``num_children`` is a column expression; ``children_per_box`` (>= 1) is the
    configured divisor.
    """
    return cast(func.ceil(num_children / float(children_per_box)), Integer)


async def resolve_children_per_box(session: "AsyncSession") -> int:
    """Read ``children_per_box`` from the singleton system settings row.

    Falls back to ``DEFAULT_CHILDREN_PER_BOX`` when no settings row exists yet
    (e.g. a fresh DB), so box-aggregating read paths don't fail before the
    settings are configured. Single home for this lookup so the fallback lives
    in one place.
    """
    from sqlmodel import select

    from app.models.system_settings import SystemSettings

    result = await session.execute(select(SystemSettings))
    system_settings = result.scalars().first()
    return (
        system_settings.children_per_box
        if system_settings
        else DEFAULT_CHILDREN_PER_BOX
    )
