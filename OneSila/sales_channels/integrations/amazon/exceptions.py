class AmazonUnsupportedPropertyForProductType(Exception):
    pass


class AmazonResponseException(Exception):
    """Raised for user-facing Amazon SP-API errors."""

    pass


class AmazonProductValidationIssuesException(Exception):
    """
    Raised when an Amazon listing submission returns validation issues.

    Intended to be treated as a user-facing exception so the remote product does not remain stuck
    in a status like PENDING_APPROVAL when approval will never come.
    """

    def __init__(self, *, issues, message: str | None = None):
        self.issues = issues or []
        super().__init__(message or self._build_message())

    def _build_message(self) -> str:
        if not self.issues:
            return "Amazon product has validation issues."

        first = self.issues[0] if isinstance(self.issues, list) and self.issues else None
        if isinstance(first, dict):
            code = first.get("code") or "unknown"
            msg = first.get("message") or "validation error"
            return f"Amazon product has validation issues ({len(self.issues)}). First: [{code}] {msg}"

        return f"Amazon product has validation issues ({len(self.issues)})."
