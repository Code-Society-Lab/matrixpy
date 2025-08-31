from typing import Optional, List, TypeVar, Generic


T = TypeVar('T')


class Paginator(Generic[T]):
    """A generic paginator for any list of items."""

    def __init__(self, items: List[T], per_page: int = 5):
        """Initialize the paginator.

        :param items: List of items to paginate
        :param per_page: Number of items per page
        """
        self.items = items
        self.per_page = per_page
        self.total_items = len(items)
        self.total_pages = max(1, -(-self.total_items // self.per_page))

    def get_page(self, page_number: int) -> 'Page[T]':
        """Get a specific page of items.

        :param page_number: Page number to retrieve (1-indexed)
        :return: Page object containing items and metadata
        """
        # Clamp page number to valid range
        page_number = max(1, min(page_number, self.total_pages))

        start_idx = (page_number - 1) * self.per_page
        end_idx = start_idx + self.per_page

        return Page(
            items=self.items[start_idx:end_idx],
            page_number=page_number,
            total_pages=self.total_pages,
            per_page=self.per_page,
            total_items=self.total_items
        )

    def get_pages(self) -> List['Page[T]']:
        """Get all pages.

        :return: List of all pages
        """
        return [self.get_page(i) for i in range(1, self.total_pages + 1)]


class Page(Generic[T]):
    """Represents a single page of paginated items."""

    def __init__(
        self,
        items: List[T],
        page_number: int,
        total_pages: int,
        per_page: int,
        total_items: int
    ):
        """Initialize a page.

        :param items: Items on this page
        :param page_number: Current page number
        :param total_pages: Total number of pages
        :param per_page: Items per page
        :param total_items: Total number of items across all pages
        """
        self.items = items
        self.page_number = page_number
        self.total_pages = total_pages
        self.per_page = per_page
        self.total_items = total_items

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page_number > 1

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page_number < self.total_pages

    @property
    def previous_page(self) -> Optional[int]:
        """Get previous page number."""
        return self.page_number - 1 if self.has_previous else None

    @property
    def next_page(self) -> Optional[int]:
        """Get next page number."""
        return self.page_number + 1 if self.has_next else None