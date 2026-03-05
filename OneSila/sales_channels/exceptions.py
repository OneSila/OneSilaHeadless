class SwitchedToCreateException(Exception):
    """Indicates that an update was attempted but no remote instance was found,
    so creation should be triggered instead."""
    pass


class SwitchedToSyncException(Exception):
    """Indicates that a create operation encountered an already-existing remote instance
    and should switch to a sync/update flow."""
    pass


class ConfigurationMissingError(Exception):
    """
    Exception raised when a configuration is missing.
    """
    pass


class PreFlightCheckError(Exception):
    """
    Exception raised when a pre-flight check fails.
    """
    pass


class VariationAlreadyExistsOnWebsite(Exception):
    """Raised when attempting to create a variation that already exists as a
    standalone product on the remote sales channel."""
    pass


class InspectorMissingInformationError(Exception):
    """Raised when a product inspector indicates missing required information."""
    pass


class ConfiguratorPropertyNotFilterable(Exception):
    """Raised when a property without filter support is used in configurator workflows."""
    pass


class RemotePropertyValueNotMapped(Exception):
    """Raised when a property value lacks a remote mapping and custom values are not allowed."""
    pass


class SkipSyncBecauseOfStatusException(Exception):
    """Raised when a remote product is in a status that should skip sync/update/create flows."""
    pass


class CombinedProductValidationError(Exception):
    """Raised when multiple user-fixable validation errors are collected in one pass."""

    def __init__(self, *, errors):
        normalized_errors = []
        for error in errors or []:
            text = str(error).strip()
            if text:
                normalized_errors.append(text)

        if not normalized_errors:
            normalized_errors = ["Product validation failed."]

        self.errors = normalized_errors
        message = "Product validation errors:\n" + "\n".join(normalized_errors)
        super().__init__(message)
