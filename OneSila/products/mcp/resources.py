from __future__ import annotations

import json

from products_inspector.constants import (
    AMAZON_REMOTE_ISSUES_ERROR,
    AMAZON_VALIDATION_ISSUES_ERROR,
    DUPLICATE_VARIATIONS_ERROR,
    ERROR_TYPES,
    HAS_IMAGES_ERROR,
    INACTIVE_BUNDLE_ITEMS_ERROR,
    ITEMS_MISSING_MANDATORY_INFORMATION_ERROR,
    MISSING_BUNDLE_ITEMS_ERROR,
    MISSING_EAN_CODE_ERROR,
    MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR,
    MISSING_OPTIONAL_PROPERTIES_ERROR,
    MISSING_PRICES_ERROR,
    MISSING_PRODUCT_TYPE_ERROR,
    MISSING_REQUIRED_PROPERTIES_ERROR,
    MISSING_STOCK_ERROR,
    MISSING_VARIATION_ERROR,
    NON_CONFIGURABLE_RULE_ERROR,
    OPTIONAL_DOCUMENT_TYPES_ERROR,
    REQUIRED_DOCUMENT_TYPES_ERROR,
    VARIATION_MISMATCH_PRODUCT_TYPE_ERROR,
    VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR,
)

_PRODUCT_INSPECTOR_ERROR_REGISTRY = (
    ("HAS_IMAGES_ERROR", HAS_IMAGES_ERROR),
    ("MISSING_PRICES_ERROR", MISSING_PRICES_ERROR),
    ("INACTIVE_BUNDLE_ITEMS_ERROR", INACTIVE_BUNDLE_ITEMS_ERROR),
    ("MISSING_VARIATION_ERROR", MISSING_VARIATION_ERROR),
    ("MISSING_BUNDLE_ITEMS_ERROR", MISSING_BUNDLE_ITEMS_ERROR),
    ("MISSING_EAN_CODE_ERROR", MISSING_EAN_CODE_ERROR),
    ("MISSING_PRODUCT_TYPE_ERROR", MISSING_PRODUCT_TYPE_ERROR),
    ("MISSING_REQUIRED_PROPERTIES_ERROR", MISSING_REQUIRED_PROPERTIES_ERROR),
    ("MISSING_OPTIONAL_PROPERTIES_ERROR", MISSING_OPTIONAL_PROPERTIES_ERROR),
    ("MISSING_STOCK_ERROR", MISSING_STOCK_ERROR),
    ("MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR", MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR),
    ("VARIATION_MISMATCH_PRODUCT_TYPE_ERROR", VARIATION_MISMATCH_PRODUCT_TYPE_ERROR),
    ("ITEMS_MISSING_MANDATORY_INFORMATION_ERROR", ITEMS_MISSING_MANDATORY_INFORMATION_ERROR),
    ("VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR", VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR),
    ("DUPLICATE_VARIATIONS_ERROR", DUPLICATE_VARIATIONS_ERROR),
    ("NON_CONFIGURABLE_RULE_ERROR", NON_CONFIGURABLE_RULE_ERROR),
    ("AMAZON_VALIDATION_ISSUES_ERROR", AMAZON_VALIDATION_ISSUES_ERROR),
    ("AMAZON_REMOTE_ISSUES_ERROR", AMAZON_REMOTE_ISSUES_ERROR),
    ("REQUIRED_DOCUMENT_TYPES_ERROR", REQUIRED_DOCUMENT_TYPES_ERROR),
    ("OPTIONAL_DOCUMENT_TYPES_ERROR", OPTIONAL_DOCUMENT_TYPES_ERROR),
)


def build_product_inspector_error_codes_payload() -> dict[str, object]:
    labels_by_code = {
        code: str(label)
        for code, label in ERROR_TYPES
    }
    codes = []
    for key, code in _PRODUCT_INSPECTOR_ERROR_REGISTRY:
        codes.append(
            {
                "code": code,
                "key": key,
                "label": labels_by_code.get(code, key.replace("_", " ").title()),
            }
        )

    return {
        "codes": codes,
    }


def register_product_mcp_resources(*, mcp) -> None:
    @mcp.resource(
        "onesila://products/inspector-error-codes",
        name="Product Inspector Error Codes",
        description="Reference list of product inspector block error codes for search_products filters.",
        mime_type="application/json",
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
        },
    )
    def get_product_inspector_error_codes() -> str:
        return json.dumps(
            build_product_inspector_error_codes_payload(),
            ensure_ascii=True,
            separators=(",", ":"),
        )
