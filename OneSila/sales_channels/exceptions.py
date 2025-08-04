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
