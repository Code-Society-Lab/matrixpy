import pytest
from matrix.help.pagination import Paginator, Page


@pytest.fixture
def sample_items():
    return list(range(1, 21))  # 20 items


def test_paginator_initialization(sample_items):
    paginator = Paginator(sample_items, per_page=5)
    assert paginator.total_items == 20
    assert paginator.per_page == 5
    assert paginator.total_pages == 4


def test_get_page_valid(sample_items):
    paginator = Paginator(sample_items, per_page=5)
    page = paginator.get_page(2)

    assert isinstance(page, Page)
    assert page.page_number == 2
    assert page.items == [6, 7, 8, 9, 10]
    assert page.total_pages == 4
    assert page.total_items == 20

    assert page.has_previous is True
    assert page.has_next is True
    assert page.previous_page == 1
    assert page.next_page == 3


def test_get_page_clamps(sample_items):
    paginator = Paginator(sample_items, per_page=5)

    first_page = paginator.get_page(0)
    assert first_page.page_number == 1
    assert first_page.items == [1, 2, 3, 4, 5]

    last_page = paginator.get_page(999)
    assert last_page.page_number == paginator.total_pages
    assert last_page.items == [16, 17, 18, 19, 20]


def test_get_pages_divisible_items():
    items = list(range(1, 10))  # 9 items
    paginator = Paginator(items, per_page=3)
    pages = paginator.get_pages()

    assert len(pages) == 3
    assert [p.items for p in pages] == [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]


def test_single_page_properties():
    items = ["a", "b"]
    paginator = Paginator(items, per_page=5)
    page = paginator.get_page(1)

    assert paginator.total_pages == 1
    assert page.page_number == 1
    assert page.items == ["a", "b"]

    assert page.has_previous is False
    assert page.has_next is False
    assert page.previous_page is None
    assert page.next_page is None


def test_empty_items():
    paginator = Paginator([], per_page=5)

    assert paginator.total_pages == 1
    page = paginator.get_page(1)

    assert page.items == []
    assert page.has_previous is False
    assert page.has_next is False
    assert page.previous_page is None
    assert page.next_page is None
