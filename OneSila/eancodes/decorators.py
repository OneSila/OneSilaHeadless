from .exceptions import ValidationError


def validation_method(func):
    """
    Decorator for validation methods that handles error reporting.

    The decorated method should return a tuple of (bool, str) where:
    - bool indicates if validation passed (True) or failed (False)
    - str contains the error message if validation failed, None otherwise

    If validation fails and fail_on_error=True, raises ValidationError with the message.
    If validation fails and fail_on_error=False, adds message to self.errors list.

    Example:
        @validation_method
        def validate_something(self):
            if error_condition:
                return False, "Validation failed because..."
            return True, None
    """

    def wrapper(self, *args, **kwargs):
        result, msg = func(self, *args, **kwargs)

        if result:
            return result, msg

        if self.fail_on_error:
            raise ValidationError(msg)
        else:
            self.errors.append(msg)
            return result, msg

    return wrapper
