class SearchFailedError(Exception):
    pass


class RequiredFieldException(Exception):
    def __init__(self, field_name, *args, **kwargs):
        message = f"Missing required field '{field_name}'."
        super().__init__(message, *args, **kwargs)


class NotDemoDataGeneratorError(Exception):
    pass
