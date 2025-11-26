class FailedToCleanupMediaStorage(Exception):
    """
    This exception is raised when the media storage cleanup fails.
    """
    pass


class NotSafeToRemoveError(Exception):
    """
    This exception is raised when the media storage cleanup is not safe to remove.
    """
    pass
