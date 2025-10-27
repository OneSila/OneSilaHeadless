class ProductFeedError(Exception):
    """Base exception for GPT product feed errors."""


class ProductFeedConfigurationError(ProductFeedError):
    """Raised when the GPT product feed is misconfigured or disabled."""


class ProductFeedValidationError(ProductFeedError):
    """Raised when product data cannot be converted into a GPT feed payload."""