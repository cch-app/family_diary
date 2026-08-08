"""Simple pagination helper shared by page routes."""

from __future__ import annotations

from dataclasses import dataclass

ALLOWED_PAGE_SIZES: tuple[int, ...] = (5, 10, 20)
DEFAULT_PAGE_SIZE = 5


def resolve_page_size(page_size: int | None) -> int:
    """Clamp an untrusted query-param page size to one of the allowed options."""
    if page_size in ALLOWED_PAGE_SIZES:
        return page_size
    return DEFAULT_PAGE_SIZE


@dataclass
class Page[T]:
    items: list[T]
    page: int
    page_size: int
    total_items: int

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 1
        return (self.total_items + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def page_numbers(self, window: int = 1) -> list[int | None]:
        """Page numbers to render as links, with None marking an ellipsis gap."""
        total = self.total_pages
        if total <= 1:
            return [1]
        keep = {1, total, self.page}
        keep.update(self.page + offset for offset in range(-window, window + 1))
        ordered = sorted(p for p in keep if 1 <= p <= total)
        result: list[int | None] = []
        prev = None
        for p in ordered:
            if prev is not None and p - prev > 1:
                result.append(None)
            result.append(p)
            prev = p
        return result


def paginate[T](items: list[T], page: int, page_size: int) -> Page[T]:
    page = max(1, page)
    start = (page - 1) * page_size
    end = start + page_size
    return Page(items=items[start:end], page=page, page_size=page_size, total_items=len(items))
