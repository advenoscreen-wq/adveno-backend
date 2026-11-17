"""Generic API response schemas shared across route groups."""

from pydantic import BaseModel


class PaginationResponse[ItemT](BaseModel):
    items: list[ItemT]
    total_pages: int
    total_items: int
    has_next: bool
    has_prev: bool
    limit: int
    page: int
