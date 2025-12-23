"""Default configuration values for the Shein integration."""

from typing import Optional

from django.utils.translation import gettext_lazy as _

from properties.models import Property

DEFAULT_TEST_API_BASE_URL = "https://openapi-test01.sheincorp.cn"
DEFAULT_PROD_API_BASE_URL = "https://openapi.sheincorp.com"

DEFAULT_TEST_AUTH_HOST = "openapi-sem-test01.dotfashion.cn"
DEFAULT_PROD_AUTH_HOST = "openapi-sem.sheincorp.com"

DEFAULT_LANGUAGE = "en"
DEFAULT_TIMEOUT = 15
DEFAULT_AES_IV = "space-station-default-iv"


# ---------------------------------------------------------------------------
# Language mapping
# ---------------------------------------------------------------------------

SHEIN_LANGUAGE_HEADER_MAP: dict[str, str] = {
    "en": "en",
    "fr": "fr",
    "es": "es",
    "de": "de",
    "zh-hans": "zh-cn",
    "th": "th",
    "pt": "pt-br",
    "pt-br": "pt-br",
}


def map_language_for_header(language_code: Optional[str]) -> str:
    """Translate a Django language code into Shein's expected header format."""

    if not language_code:
        return DEFAULT_LANGUAGE

    normalised = language_code.lower()
    return SHEIN_LANGUAGE_HEADER_MAP.get(normalised, DEFAULT_LANGUAGE)


# ---------------------------------------------------------------------------
# Remote metadata
# ---------------------------------------------------------------------------

SHEIN_LANGUAGE_CATALOG: list[dict[str, str]] = [
    {
        "shein_domain": "us.shein.com",
        "language_code": "en",
        "language_name": "English",
    },
    {
        "shein_domain": "us.shein.com",
        "language_code": "es",
        "language_name": "Spanish",
    },
    {
        "shein_domain": "roe.shein.com",
        "language_code": "en",
        "language_name": "English",
    },
    {
        "shein_domain": "de.shein.com",
        "language_code": "de",
        "language_name": "German",
    },
    {
        "shein_domain": "eur.shein.com",
        "language_code": "en",
        "language_name": "English",
    },
    {
        "shein_domain": "eur.shein.com",
        "language_code": "bg",
        "language_name": "Bulgarian",
    },
    {
        "shein_domain": "fr.shein.com",
        "language_code": "fr",
        "language_name": "French",
    },
    {
        "shein_domain": "it.shein.com",
        "language_code": "it",
        "language_name": "Italian",
    },
    {
        "shein_domain": "ch.shein.com",
        "language_code": "de",
        "language_name": "German",
    },
    {
        "shein_domain": "ch.shein.com",
        "language_code": "fr",
        "language_name": "French",
    },
    {
        "shein_domain": "pl.shein.com",
        "language_code": "pl",
        "language_name": "Polish",
    },
    {
        "shein_domain": "pt.shein.com",
        "language_code": "pt",
        "language_name": "Portuguese",
    },
    {
        "shein_domain": "es.shein.com",
        "language_code": "es",
        "language_name": "Spanish",
    },
    {
        "shein_domain": "www.shein.se",
        "language_code": "en",
        "language_name": "English",
    },
    {
        "shein_domain": "www.shein.se",
        "language_code": "sv",
        "language_name": "Swedish",
    },
    {
        "shein_domain": "www.shein.co.uk",
        "language_code": "en",
        "language_name": "English",
    },
]


# ---------------------------------------------------------------------------
# Internal property definitions
# ---------------------------------------------------------------------------

SHEIN_PACKAGE_TYPE_OPTIONS = [
    {"value": "0", "label": _("Clear packaging")},
    {"value": "1", "label": _("Soft packaging + soft item")},
    {"value": "2", "label": _("Soft packaging + hard item")},
    {"value": "3", "label": _("Hard packaging")},
    {"value": "4", "label": _("Vacuum")},
]

SHEIN_QUANTITY_UNIT_OPTIONS = [
    {"value": "1", "label": _("Piece")},
    {"value": "2", "label": _("Pair")},
]

SHEIN_INTERNAL_PROPERTY_DEFINITIONS = [
    {
        "code": "supplier_code",
        "name": _("Supplier code"),
        "type": Property.TYPES.TEXT,
        "payload_field": "supplier_code",
    },
    {
        "code": "reference_product_link",
        "name": _("Reference product link"),
        "type": Property.TYPES.TEXT,
        "payload_field": "competing_product_link",
    },
    {
        "code": "brand_code",
        "name": _("Brand"),
        "type": Property.TYPES.SELECT,
        "payload_field": "brand_code",
    },
    {
        "code": "package_type",
        "name": _("Package type"),
        "type": Property.TYPES.SELECT,
        "payload_field": "package_type",
        "options": SHEIN_PACKAGE_TYPE_OPTIONS,
    },
    {
        "code": "quantity_info__unit",
        "name": _("Quantity unit"),
        "type": Property.TYPES.SELECT,
        "payload_field": "quantity_unit",
        "options": SHEIN_QUANTITY_UNIT_OPTIONS,
    },
    {
        "code": "quantity_info__quantity",
        "name": _("Quantity"),
        "type": Property.TYPES.INT,
        "payload_field": "quantity",
    },
    {
        "code": "height",
        "name": _("Package height (cm)"),
        "type": Property.TYPES.FLOAT,
        "payload_field": "height",
    },
    {
        "code": "length",
        "name": _("Package length (cm)"),
        "type": Property.TYPES.FLOAT,
        "payload_field": "length",
    },
    {
        "code": "width",
        "name": _("Package width (cm)"),
        "type": Property.TYPES.FLOAT,
        "payload_field": "width",
    },
    {
        "code": "weight",
        "name": _("Package weight (g)"),
        "type": Property.TYPES.INT,
        "payload_field": "weight",
    },
]
