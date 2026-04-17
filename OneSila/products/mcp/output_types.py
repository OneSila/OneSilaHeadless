from __future__ import annotations

from properties.mcp.output_types import (
    COMPANY_LANGUAGE_OUTPUT_SCHEMA,
    PROPERTY_REFERENCE_OUTPUT_SCHEMA,
    PROPERTY_SELECT_VALUE_SUMMARY_OUTPUT_SCHEMA,
    PROPERTY_SELECT_VALUE_TRANSLATION_OUTPUT_SCHEMA,
)


PRODUCT_TYPE_ENUM = ["SIMPLE", "BUNDLE", "CONFIGURABLE", "ALIAS"]
PRODUCT_IMAGE_TYPE_ENUM = ["MOOD", "PACK", "COLOR"]
SCALAR_VALUE_VARIANTS = [
    {"type": "string"},
    {"type": "number"},
    {"type": "boolean"},
    {"type": "null"},
]
VALUE_SCHEMA = {
    "oneOf": SCALAR_VALUE_VARIANTS
    + [
        {
            "type": "array",
            "items": {
                "oneOf": SCALAR_VALUE_VARIANTS,
            },
        }
    ],
}


PRODUCT_VAT_RATE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": ["string", "null"]},
        "rate": {"type": ["integer", "null"]},
    },
    "required": ["id", "name", "rate"],
}


PRODUCT_INSPECTOR_ISSUE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "integer"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "fixing_message": {"type": ["string", "null"]},
    },
    "required": ["code", "title", "description", "fixing_message"],
}


PRODUCT_INSPECTOR_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "has_inspector": {"type": "boolean"},
        "has_missing_required_information": {"type": "boolean"},
        "has_missing_optional_information": {"type": "boolean"},
        "has_missing_information": {"type": "boolean"},
        "status_code": {"type": ["integer", "null"]},
        "status_label": {
            "type": ["string", "null"],
            "enum": ["green", "orange", "red", None],
        },
        "issues": {
            "type": "array",
            "items": PRODUCT_INSPECTOR_ISSUE_OUTPUT_SCHEMA,
        },
    },
    "required": [
        "has_inspector",
        "has_missing_required_information",
        "has_missing_optional_information",
        "has_missing_information",
        "status_code",
        "status_label",
        "issues",
    ],
}


SALES_CHANNEL_REFERENCE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "hostname": {"type": "string"},
        "active": {"type": "boolean"},
        "type": {"type": "string"},
        "subtype": {"type": ["string", "null"]},
    },
    "required": ["id", "hostname", "active", "type", "subtype"],
}


PRODUCT_IMAGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "image_url": {"type": ["string", "null"]},
        "thumbnail_url": {"type": ["string", "null"]},
        "type": {
            "type": ["string", "null"],
            "enum": PRODUCT_IMAGE_TYPE_ENUM + [None],
        },
        "title": {"type": ["string", "null"]},
        "description": {"type": ["string", "null"]},
        "is_main_image": {"type": "boolean"},
        "sort_order": {"type": "integer"},
        "sales_channel": {
            "oneOf": [
                SALES_CHANNEL_REFERENCE_OUTPUT_SCHEMA,
                {"type": "null"},
            ],
        },
    },
    "required": [
        "image_url",
        "thumbnail_url",
        "type",
        "title",
        "description",
        "is_main_image",
        "sort_order",
        "sales_channel",
    ],
}


PRODUCT_PRICE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "currency": {"type": "string"},
        "rrp": {"type": ["string", "null"]},
        "price": {"type": ["string", "null"]},
    },
    "required": ["currency", "rrp", "price"],
}


PRODUCT_TRANSLATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string"},
        "name": {"type": "string"},
        "sales_channel": {
            "oneOf": [
                SALES_CHANNEL_REFERENCE_OUTPUT_SCHEMA,
                {"type": "null"},
            ],
        },
        "subtitle": {"type": "string"},
        "short_description": {"type": "string"},
        "description": {"type": "string"},
        "url_key": {"type": "string"},
        "bullet_points": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["language", "name", "sales_channel"],
}


PRODUCT_ASSIGNED_PROPERTY_VALUE_TRANSLATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string"},
        "value": VALUE_SCHEMA,
    },
    "required": ["language", "value"],
}


PRODUCT_ASSIGNED_PROPERTY_VALUE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": ["integer", "null"]},
        "value": VALUE_SCHEMA,
        "translations": {
            "type": "array",
            "items": PRODUCT_ASSIGNED_PROPERTY_VALUE_TRANSLATION_OUTPUT_SCHEMA,
        },
    },
    "required": ["id", "value", "translations"],
}


PRODUCT_ASSIGNED_PROPERTY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "property": PROPERTY_REFERENCE_OUTPUT_SCHEMA,
        "value": VALUE_SCHEMA,
        "values": {
            "type": "array",
            "items": PRODUCT_ASSIGNED_PROPERTY_VALUE_OUTPUT_SCHEMA,
        },
    },
    "required": ["property", "value", "values"],
}


PRODUCT_REQUIREMENT_TYPE_ENUM = [
    "REQUIRED_IN_CONFIGURATOR",
    "OPTIONAL_IN_CONFIGURATOR",
    "REQUIRED",
    "OPTIONAL",
]


PRODUCT_REQUIREMENT_PRODUCT_TYPE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "select_value": {"type": "string"},
    },
    "required": ["id", "select_value"],
}


PRODUCT_PROPERTY_REQUIREMENT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "property_id": {"type": "integer"},
        "property_name": {"type": "string"},
        "requirement_type": {
            "type": "string",
            "enum": PRODUCT_REQUIREMENT_TYPE_ENUM,
        },
        "effectively_required": {"type": "boolean"},
        "has_value": {"type": "boolean"},
        "current_value_summary": {"type": ["string", "null"]},
    },
    "required": [
        "property_id",
        "property_name",
        "requirement_type",
        "effectively_required",
        "has_value",
        "current_value_summary",
    ],
}


PRODUCT_PROPERTY_REQUIREMENTS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "product_type": {
            "oneOf": [
                PRODUCT_REQUIREMENT_PRODUCT_TYPE_OUTPUT_SCHEMA,
                {"type": "null"},
            ],
        },
        "requirements": {
            "type": "object",
            "additionalProperties": PRODUCT_PROPERTY_REQUIREMENT_OUTPUT_SCHEMA,
        },
    },
    "required": ["product_type", "requirements"],
}


PRODUCT_SEARCH_SUMMARY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "sku": {"type": ["string", "null"]},
        "name": {"type": "string"},
        "type": {"type": "string", "enum": PRODUCT_TYPE_ENUM},
        "type_label": {"type": "string"},
        "active": {"type": "boolean"},
        "vat_rate": {"type": ["integer", "null"]},
        "thumbnail_url": {"type": ["string", "null"]},
        "has_images": {"type": "boolean"},
        "has_missing_required_information": {"type": "boolean"},
        "has_missing_optional_information": {"type": "boolean"},
        "has_missing_information": {"type": "boolean"},
    },
    "required": [
        "id",
        "sku",
        "name",
        "type",
        "type_label",
        "active",
        "vat_rate",
        "thumbnail_url",
        "has_images",
        "has_missing_required_information",
        "has_missing_optional_information",
        "has_missing_information",
    ],
}


PRODUCT_BASE_DETAIL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "sku": {"type": ["string", "null"]},
        "name": {"type": "string"},
        "type": {"type": "string", "enum": PRODUCT_TYPE_ENUM},
        "type_label": {"type": "string"},
        "active": {"type": "boolean"},
        "vat_rate": {"type": ["integer", "null"]},
        "thumbnail_url": {"type": ["string", "null"]},
        "has_images": {"type": "boolean"},
        "onesila_url": {"type": "string"},
        "allow_backorder": {"type": "boolean"},
    },
    "required": [
        "id",
        "sku",
        "name",
        "type",
        "type_label",
        "active",
        "vat_rate",
        "thumbnail_url",
        "has_images",
        "onesila_url",
        "allow_backorder",
    ],
}


PRODUCT_BRAND_VOICE_LANGUAGE_PROMPT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string"},
        "prompt": {"type": "string"},
    },
    "required": ["language", "prompt"],
}


PRODUCT_BRAND_VOICE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "brand_value_id": {"type": "integer"},
        "brand_value": {"type": "string"},
        "default_prompt": {"type": "string"},
        "language_prompts": {
            "type": "array",
            "items": PRODUCT_BRAND_VOICE_LANGUAGE_PROMPT_OUTPUT_SCHEMA,
        },
    },
    "required": ["brand_value_id", "brand_value"],
}


GET_PRODUCT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        **PRODUCT_BASE_DETAIL_OUTPUT_SCHEMA["properties"],
        "vat_rate_data": {
            "oneOf": [
                PRODUCT_VAT_RATE_OUTPUT_SCHEMA,
                {"type": "null"},
            ],
        },
        "inspector": PRODUCT_INSPECTOR_OUTPUT_SCHEMA,
        "property_requirements": PRODUCT_PROPERTY_REQUIREMENTS_OUTPUT_SCHEMA,
        "translations": {
            "type": "array",
            "items": PRODUCT_TRANSLATION_OUTPUT_SCHEMA,
        },
        "images": {
            "type": "array",
            "items": PRODUCT_IMAGE_OUTPUT_SCHEMA,
        },
        "properties": {
            "type": "array",
            "items": PRODUCT_ASSIGNED_PROPERTY_OUTPUT_SCHEMA,
        },
        "prices": {
            "type": "array",
            "items": PRODUCT_PRICE_OUTPUT_SCHEMA,
        },
        "brand_voice": {
            "oneOf": [
                PRODUCT_BRAND_VOICE_OUTPUT_SCHEMA,
                {"type": "null"},
            ],
        },
    },
    "required": PRODUCT_BASE_DETAIL_OUTPUT_SCHEMA["required"],
}


SEARCH_PRODUCTS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "total_count": {"type": "integer"},
        "has_more": {"type": "boolean"},
        "offset": {"type": "integer"},
        "limit": {"type": "integer"},
        "results": {
            "type": "array",
            "items": PRODUCT_SEARCH_SUMMARY_OUTPUT_SCHEMA,
        },
    },
    "required": ["total_count", "has_more", "offset", "limit", "results"],
}


VAT_RATE_OPTION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": ["string", "null"]},
        "rate": {"type": ["integer", "null"]},
    },
    "required": ["id", "name", "rate"],
}


COMPANY_PRODUCT_TYPE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "value": {"type": "string"},
        "translations": {
            "type": "array",
            "items": PROPERTY_SELECT_VALUE_TRANSLATION_OUTPUT_SCHEMA,
        },
        "usage_count": {"type": "integer"},
    },
    "required": ["id", "value"],
}


COMPANY_PRODUCT_TYPES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "count": {"type": "integer"},
        "property": PROPERTY_REFERENCE_OUTPUT_SCHEMA,
        "results": {
            "type": "array",
            "items": COMPANY_PRODUCT_TYPE_OUTPUT_SCHEMA,
        },
    },
    "required": ["count", "property", "results"],
}


GET_PRODUCT_TYPES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "count": {"type": "integer"},
        "property": PROPERTY_REFERENCE_OUTPUT_SCHEMA,
        "results": {
            "type": "array",
            "items": PROPERTY_SELECT_VALUE_SUMMARY_OUTPUT_SCHEMA,
        },
    },
    "required": ["count", "property", "results"],
}


GET_VAT_RATES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "count": {"type": "integer"},
        "results": {
            "type": "array",
            "items": VAT_RATE_OPTION_OUTPUT_SCHEMA,
        },
    },
    "required": ["count", "results"],
}


COMPANY_CURRENCY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "iso_code": {"type": "string"},
        "name": {"type": "string"},
        "symbol": {"type": "string"},
        "is_default": {"type": "boolean"},
        "inherits_from_iso_code": {"type": ["string", "null"]},
    },
    "required": ["id", "iso_code", "name", "symbol", "is_default", "inherits_from_iso_code"],
}


COMPANY_CURRENCIES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "count": {"type": "integer"},
        "default_currency_code": {"type": ["string", "null"]},
        "results": {
            "type": "array",
            "items": COMPANY_CURRENCY_OUTPUT_SCHEMA,
        },
    },
    "required": ["count", "default_currency_code", "results"],
}


GET_COMPANY_DETAILS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "languages": {
            "type": "object",
            "properties": {
                "default_language_code": {"type": "string"},
                "enabled_languages": {
                    "type": "array",
                    "items": COMPANY_LANGUAGE_OUTPUT_SCHEMA,
                },
            },
            "required": ["default_language_code", "enabled_languages"],
        },
        "product_types": COMPANY_PRODUCT_TYPES_OUTPUT_SCHEMA,
        "vat_rates": GET_VAT_RATES_OUTPUT_SCHEMA,
        "currencies": COMPANY_CURRENCIES_OUTPUT_SCHEMA,
    },
}


SEARCH_SALES_CHANNELS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "total_count": {"type": "integer"},
        "has_more": {"type": "boolean"},
        "offset": {"type": "integer"},
        "limit": {"type": "integer"},
        "results": {
            "type": "array",
            "items": SALES_CHANNEL_REFERENCE_OUTPUT_SCHEMA,
        },
    },
    "required": ["total_count", "has_more", "offset", "limit", "results"],
}


PRODUCT_UPSERT_APPLIED_UPDATES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "active": {"type": "boolean"},
        "ean_code": {"type": "boolean"},
        "translations": {"type": "integer"},
        "prices": {"type": "integer"},
        "properties": {"type": "integer"},
        "images": {"type": "integer"},
    },
}


PRODUCT_UPSERT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "updated": {"type": "boolean"},
        "product_id": {"type": "integer"},
        "sku": {"type": ["string", "null"]},
        "name": {"type": "string"},
        "active": {"type": "boolean"},
        "message": {"type": "string"},
        "applied_updates": PRODUCT_UPSERT_APPLIED_UPDATES_OUTPUT_SCHEMA,
    },
    "required": ["updated", "product_id", "sku", "name", "message", "applied_updates"],
}


CREATE_PRODUCT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "created": {"type": "boolean"},
        "sku_was_generated": {"type": "boolean"},
        "product_id": {"type": "integer"},
        "sku": {"type": ["string", "null"]},
        "name": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["created", "sku_was_generated", "product_id", "sku", "name", "message"],
}
