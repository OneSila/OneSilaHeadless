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

        if isinstance(self.issues, list):
            details = []
            for issue in self.issues:
                if isinstance(issue, dict):
                    code = issue.get("code") or "unknown"
                    msg = issue.get("message") or "validation error"
                    details.append(f"- [{code}] {msg}")
                else:
                    details.append(f"- {issue}")

            if details:
                return "Amazon product has validation issues ({}).\n{}".format(
                    len(self.issues),
                    "\n".join(details),
                )

        return "Amazon product has validation issues ({}).".format(len(self.issues))


class AmazonTitleTooShortError(Exception):
    """Raised when Amazon listing titles are below the required length."""
    pass


class AmazonDescriptionTooShortError(Exception):
    """Raised when Amazon listing descriptions are below the required length."""
    pass


class AmazonMissingIdentifierError(Exception):
    """Raised when an Amazon listing lacks a required product identifier."""
    pass


class AmazonMissingVariationIdentifierError(Exception):
    """Raised when Amazon variations lack required identifiers."""
    pass


class AmazonMissingBrowseNodeError(Exception):
    """Raised when Amazon browse node mappings are missing for first assignment."""
    pass


class AmazonMissingVariationThemeError(Exception):
    """Raised when Amazon variation theme mappings are missing for first assignment."""
    pass


class AmazonProductTypeNotMappedError(Exception):
    """Raised when no Amazon product type mapping exists for the selected rule."""
    pass
