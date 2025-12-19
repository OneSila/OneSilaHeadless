from __future__ import annotations


class EbayTemporarySystemError(Exception):
    """Raised when eBay returns a temporary system error after retries."""

