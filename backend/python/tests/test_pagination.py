"""
Unit tests for the pagination schema and utility.

Tests cover:
- PaginationParams defaults, offset/limit calculation, validation
- PaginatedResponse.create() total_pages calculation and edge cases
"""

import pytest

from app.schemas.pagination import PaginatedResponse, PaginationParams


class TestPaginationParams:
    """Test suite for PaginationParams."""

    def test_defaults(self) -> None:
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 50
        assert params.offset == 0
        assert params.limit == 50

    def test_page_2(self) -> None:
        params = PaginationParams(page=2, page_size=25)
        assert params.offset == 25
        assert params.limit == 25

    def test_page_3(self) -> None:
        params = PaginationParams(page=3, page_size=10)
        assert params.offset == 20
        assert params.limit == 10

    def test_invalid_page_zero(self) -> None:
        with pytest.raises(ValueError):
            PaginationParams(page=0)

    def test_invalid_negative_page(self) -> None:
        with pytest.raises(ValueError):
            PaginationParams(page=-1)

    def test_invalid_page_size_zero(self) -> None:
        with pytest.raises(ValueError):
            PaginationParams(page_size=0)

    def test_invalid_page_size_too_large(self) -> None:
        with pytest.raises(ValueError):
            PaginationParams(page_size=201)


class TestPaginatedResponse:
    """Test suite for PaginatedResponse."""

    def test_create(self) -> None:
        resp = PaginatedResponse.create(
            items=["a", "b", "c"], total=10, page=1, page_size=3
        )
        assert resp.items == ["a", "b", "c"]
        assert resp.total == 10
        assert resp.page == 1
        assert resp.page_size == 3
        assert resp.total_pages == 4  # ceil(10/3)

    def test_create_exact_division(self) -> None:
        resp = PaginatedResponse.create(
            items=list(range(5)), total=15, page=1, page_size=5
        )
        assert resp.total_pages == 3

    def test_create_empty(self) -> None:
        resp: PaginatedResponse[int] = PaginatedResponse.create(items=[], total=0, page=1, page_size=50)
        assert resp.total_pages == 0
        assert resp.items == []

    def test_create_single_page(self) -> None:
        resp = PaginatedResponse.create(items=[1, 2, 3], total=3, page=1, page_size=50)
        assert resp.total_pages == 1

    def test_create_last_partial_page(self) -> None:
        resp = PaginatedResponse.create(items=[1], total=51, page=2, page_size=50)
        assert resp.total_pages == 2
        assert resp.page == 2
