from __future__ import annotations


class EbayResponseException(Exception):
    """User-facing exception for eBay API errors."""
    pass


class EbayTemporarySystemError(Exception):
    """Raised when eBay returns a temporary system error after retries."""
    pass
