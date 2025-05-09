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
