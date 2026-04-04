from __future__ import annotations

from properties.mcp.output_types import (
    PROPERTY_REFERENCE_OUTPUT_SCHEMA,
    PROPERTY_SELECT_VALUE_SUMMARY_OUTPUT_SCHEMA,
)


PRODUCT_TYPE_ENUM = ["SIMPLE", "BUNDLE", "CONFIGURABLE", "ALIAS"]
PRODUCT_IMAGE_TYPE_ENUM = ["MOOD", "PACK", "COLOR"]
SCALAR_VALUE_VARIANTS = [
    {"type": "string"},
    {"type": "integer"},
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
        "sales_channel_id": {"type": ["integer", "null"]},
    },
    "required": [
        "image_url",
        "thumbnail_url",
        "type",
        "title",
        "description",
        "is_main_image",
        "sort_order",
        "sales_channel_id",
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
        "sales_channel": {"type": ["integer", "null"]},
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


PRODUCT_SUMMARY_OUTPUT_SCHEMA = {
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


GET_PRODUCT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        **PRODUCT_SUMMARY_OUTPUT_SCHEMA["properties"],
        "allow_backorder": {"type": "boolean"},
        "vat_rate_data": {
            "oneOf": [
                PRODUCT_VAT_RATE_OUTPUT_SCHEMA,
                {"type": "null"},
            ],
        },
        "inspector": PRODUCT_INSPECTOR_OUTPUT_SCHEMA,
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
    },
    "required": PRODUCT_SUMMARY_OUTPUT_SCHEMA["required"]
    + [
        "allow_backorder",
        "vat_rate_data",
        "inspector",
        "translations",
        "images",
        "properties",
        "prices",
    ],
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
            "items": PRODUCT_SUMMARY_OUTPUT_SCHEMA,
        },
    },
    "required": ["total_count", "has_more", "offset", "limit", "results"],
}


GET_PRODUCT_FRONTEND_URL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "sku": {"type": ["string", "null"]},
        "global_id": {"type": "string"},
        "frontend_path": {"type": "string"},
        "frontend_url": {"type": "string"},
    },
    "required": ["id", "sku", "global_id", "frontend_path", "frontend_url"],
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


PRODUCT_MUTATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "updated": {"type": "boolean"},
        "product": GET_PRODUCT_OUTPUT_SCHEMA,
    },
    "required": ["updated", "product"],
}


PRODUCT_BATCH_MUTATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "updated_count": {"type": "integer"},
        "product": GET_PRODUCT_OUTPUT_SCHEMA,
    },
    "required": ["updated_count", "product"],
}


CREATE_PRODUCT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "created": {"type": "boolean"},
        "sku_was_generated": {"type": "boolean"},
        "product": GET_PRODUCT_OUTPUT_SCHEMA,
    },
    "required": ["created", "sku_was_generated", "product"],
}
