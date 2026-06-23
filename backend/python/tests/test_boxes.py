"""Tests for app.utilities.boxes — the single source of truth for box math.

Box counts are derived as ceil(num_children / children_per_box). These tests
cover the pure helper (compute_boxes), the SQL expression (box_count_expr), and
the settings lookup with its fallback (resolve_children_per_box).
"""

import pytest
from sqlalchemy import literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.system_settings import SystemSettings
from app.utilities.boxes import (
    DEFAULT_CHILDREN_PER_BOX,
    box_count_expr,
    compute_boxes,
    resolve_children_per_box,
)


class TestComputeBoxes:
    """Pure ceil-division behaviour and input validation."""

    @pytest.mark.parametrize(
        ("num_children", "children_per_box", "expected"),
        [
            # divisor of 2 (the common case): exact, off-by-one, and zero
            (0, 2, 0),
            (1, 2, 1),
            (2, 2, 1),
            (3, 2, 2),
            (4, 2, 2),
            (5, 2, 3),
            # divisor of 1 is the identity
            (0, 1, 0),
            (5, 1, 5),
            (10, 1, 10),
            # divisor of 3: boundaries around each multiple
            (6, 3, 2),
            (7, 3, 3),
            (9, 3, 3),
            (10, 3, 4),
            # divisor larger than the count
            (3, 5, 1),
            (5, 5, 1),
            (6, 5, 2),
            # larger magnitudes
            (100, 10, 10),
            (101, 10, 11),
        ],
    )
    def test_ceil_division(
        self, num_children: int, children_per_box: int, expected: int
    ) -> None:
        assert compute_boxes(num_children, children_per_box) == expected

    @pytest.mark.parametrize("bad_children_per_box", [0, -1, -5])
    def test_rejects_non_positive_divisor(self, bad_children_per_box: int) -> None:
        with pytest.raises(ValueError, match="children_per_box"):
            compute_boxes(4, bad_children_per_box)

    @pytest.mark.parametrize("bad_num_children", [-1, -10])
    def test_rejects_negative_children(self, bad_num_children: int) -> None:
        with pytest.raises(ValueError, match="num_children"):
            compute_boxes(bad_num_children, 2)


class TestResolveChildrenPerBox:
    """The settings lookup falls back to the default when no row exists."""

    @pytest.mark.asyncio
    async def test_defaults_when_no_settings_row(
        self, test_session: AsyncSession
    ) -> None:
        assert await resolve_children_per_box(test_session) == DEFAULT_CHILDREN_PER_BOX

    @pytest.mark.asyncio
    async def test_reads_configured_value(self, test_session: AsyncSession) -> None:
        test_session.add(SystemSettings(children_per_box=7))
        await test_session.commit()
        assert await resolve_children_per_box(test_session) == 7


class TestBoxCountExpr:
    """The SQL expression must agree with the Python helper."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("num_children", "children_per_box"),
        [(0, 2), (1, 2), (5, 2), (10, 3), (7, 3), (5, 1), (6, 5), (101, 10)],
    )
    async def test_matches_compute_boxes(
        self, test_session: AsyncSession, num_children: int, children_per_box: int
    ) -> None:
        value = (
            await test_session.execute(
                select(box_count_expr(literal(num_children), children_per_box))
            )
        ).scalar_one()
        assert value == compute_boxes(num_children, children_per_box)
