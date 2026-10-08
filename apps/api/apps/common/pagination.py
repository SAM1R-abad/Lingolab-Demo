import os

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Shared pagination for admin bulk list endpoints (users, question bank).

    Not wired in as DRF's global DEFAULT_PAGINATION_CLASS on purpose: most
    endpoints in this API return small, naturally-bounded data (a single
    session's current batch, a user's own session history, etc.) where
    pagination would only add noise. This class is opt-in, applied per-view
    only where a list can grow unbounded with real usage (all users, all
    questions in the bank).

    `page_size` defaults to 50 (configurable via DEFAULT_PAGE_SIZE env var)
    and clients may request a smaller/larger page via `?page_size=`, capped
    at `max_page_size` to prevent an accidental/abusive single huge query.
    """

    page_size = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
    page_size_query_param = "page_size"
    max_page_size = 200
