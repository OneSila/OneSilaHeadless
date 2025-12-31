class SheinResponseException(Exception):
    """Raised when Shein returns an application-level error response."""


class SheinPreValidationError(SheinResponseException):
    """Raised when Shein returns success=false in the response info payload."""


class SheinConfiguratorAttributesLimitError(SheinResponseException):
    """Raised when too many configurator attributes are provided for a Shein product (more than three total)."""
