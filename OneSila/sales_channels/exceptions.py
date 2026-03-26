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


class MissingMappingError(PreFlightCheckError):
    """
    Exception raised when a required channel mapping is missing.
    """
    pass


class MiraklPayloadValidationError(PreFlightCheckError):
    """Raised when a value cannot satisfy Mirakl-side payload validations."""

    pass


class MiraklImportMissingFilesError(PreFlightCheckError):
    """Raised when a Mirakl product import is started without any export files."""

    pass


class MiraklImportInvalidFileTypeError(PreFlightCheckError):
    """Raised when a Mirakl import export file is not an .xlsx workbook."""

    pass


class MiraklImportInvalidFileLayoutError(PreFlightCheckError):
    """Raised when a Mirakl import export file does not match the expected workbook layout."""

    pass


class MiraklImportMissingProductSkuError(PreFlightCheckError):
    """Raised when an XLSX row does not provide the required Mirakl product_sku field."""

    pass


class MiraklImportConfigurableConflictError(PreFlightCheckError):
    """Raised when a configurable SKU resolves to an incompatible existing local product."""

    pass


class MiraklImportInvalidRowError(PreFlightCheckError):
    """Raised when an XLSX row cannot be normalized into a valid Mirakl import payload."""

    pass


class MiraklNewProductReportLookupError(Exception):
    """Raised when a Mirakl added-products report cannot be resolved back to remote product details."""

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
