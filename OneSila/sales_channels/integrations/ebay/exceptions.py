"""Custom exception classes for eBay integration."""


class EbayResponseException(Exception):
    """Raised when eBay returns a handled API error meant for end-users."""

    pass
