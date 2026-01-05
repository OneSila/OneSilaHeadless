from __future__ import annotations

from sales_channels.exceptions import PreFlightCheckError


class EbayResponseException(Exception):
    """User-facing exception for eBay API errors."""
    pass


class EbayTemporarySystemError(Exception):
    """Raised when eBay returns a temporary system error after retries."""
    pass


class EbayPropertyMappingMissingError(PreFlightCheckError):
    """Raised when a local property lacks an eBay aspect mapping."""
    pass
