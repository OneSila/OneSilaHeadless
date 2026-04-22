from __future__ import annotations


PROPERTY_TYPE_ENUM = [
    "INT",
    "FLOAT",
    "TEXT",
    "DESCRIPTION",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "SELECT",
    "MULTISELECT",
]

PROPERTY_TRANSLATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string"},
        "name": {"type": "string"},
    },
    "required": ["language", "name"],
}

COMPANY_LANGUAGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "name": {"type": "string"},
        "name_local": {"type": "string"},
        "name_translated": {"type": "string"},
        "bidi": {"type": "boolean"},
        "is_default": {"type": "boolean"},
    },
    "required": ["code", "name", "name_local", "name_translated", "bidi", "is_default"],
}

PROPERTY_SELECT_VALUE_TRANSLATION_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string"},
        "value": {"type": "string"},
    },
    "required": ["language", "value"],
}

PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "value": {"type": "string"},
        "translations": {
            "type": "array",
            "items": PROPERTY_SELECT_VALUE_TRANSLATION_OUTPUT_SCHEMA,
        },
    },
    "required": ["id", "value", "translations"],
}

PROPERTY_SUMMARY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "internal_name": {"type": ["string", "null"]},
        "type": {
            "type": "string",
            "enum": PROPERTY_TYPE_ENUM,
        },
        "type_label": {"type": "string"},
        "is_public_information": {"type": "boolean"},
        "add_to_filters": {"type": "boolean"},
        "has_image": {"type": "boolean"},
    },
    "required": [
        "id",
        "name",
        "internal_name",
        "type",
        "type_label",
        "is_public_information",
        "add_to_filters",
        "has_image",
    ],
}

PROPERTY_REFERENCE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "internal_name": {"type": ["string", "null"]},
        "type": {
            "type": "string",
            "enum": PROPERTY_TYPE_ENUM,
        },
        "type_label": {"type": "string"},
        "is_product_type": {"type": "boolean"},
    },
    "required": [
        "id",
        "name",
        "internal_name",
        "type",
        "type_label",
        "is_product_type",
    ],
}

SEARCH_PROPERTIES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "total_count": {"type": "integer"},
        "has_more": {"type": "boolean"},
        "offset": {"type": "integer"},
        "limit": {"type": "integer"},
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    **PROPERTY_SUMMARY_OUTPUT_SCHEMA["properties"],
                    "translations": {
                        "type": "array",
                        "items": PROPERTY_TRANSLATION_OUTPUT_SCHEMA,
                    },
                },
                "required": PROPERTY_SUMMARY_OUTPUT_SCHEMA["required"],
            },
        },
    },
    "required": ["total_count", "has_more", "offset", "limit", "results"],
}

PROPERTY_SELECT_VALUE_SUMMARY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "value": {"type": "string"},
        "full_value_name": {"type": "string"},
        "usage_count": {"type": "integer"},
        "thumbnail_url": {"type": ["string", "null"]},
        "property": PROPERTY_REFERENCE_OUTPUT_SCHEMA,
    },
    "required": [
        "id",
        "value",
        "full_value_name",
        "usage_count",
        "thumbnail_url",
        "property",
    ],
}

PROPERTY_SELECT_VALUE_DETAIL_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        **PROPERTY_SELECT_VALUE_SUMMARY_OUTPUT_SCHEMA["properties"],
        "translations": {
            "type": "array",
            "items": PROPERTY_SELECT_VALUE_TRANSLATION_OUTPUT_SCHEMA,
        },
    },
    "required": [
        *PROPERTY_SELECT_VALUE_SUMMARY_OUTPUT_SCHEMA["required"],
        "translations",
    ],
}

SEARCH_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "total_count": {"type": "integer"},
        "has_more": {"type": "boolean"},
        "offset": {"type": "integer"},
        "limit": {"type": "integer"},
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "value": {"type": "string"},
                    "thumbnail_url": {"type": ["string", "null"]},
                    "property": PROPERTY_REFERENCE_OUTPUT_SCHEMA,
                    "usage_count": {"type": "integer"},
                    "translations": {
                        "type": "array",
                        "items": PROPERTY_SELECT_VALUE_TRANSLATION_OUTPUT_SCHEMA,
                    },
                },
                "required": ["id", "value", "thumbnail_url", "property"],
            },
        },
    },
    "required": ["total_count", "has_more", "offset", "limit", "results"],
}

GET_PROPERTY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        **PROPERTY_SUMMARY_OUTPUT_SCHEMA["properties"],
        "is_product_type": {"type": "boolean"},
        "translations": {
            "type": "array",
            "items": PROPERTY_TRANSLATION_OUTPUT_SCHEMA,
        },
        "values": {
            "type": "array",
            "items": PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA,
        },
    },
    "required": [
        *PROPERTY_SUMMARY_OUTPUT_SCHEMA["required"],
        "is_product_type",
        "translations",
        "values",
    ],
}

GET_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA = PROPERTY_SELECT_VALUE_DETAIL_OUTPUT_SCHEMA

CREATE_PROPERTY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "created": {"type": "boolean"},
        "property_id": {"type": "integer"},
        "internal_name": {"type": ["string", "null"]},
        "name": {"type": "string"},
        "type": {
            "type": "string",
            "enum": PROPERTY_TYPE_ENUM,
        },
        "type_label": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["created", "property_id", "internal_name", "name", "type", "type_label", "message"],
}

CREATE_PROPERTIES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "requested_count": {"type": "integer"},
        "processed_count": {"type": "integer"},
        "created_count": {"type": "integer"},
        "updated_existing_count": {"type": "integer"},
        "results": {
            "type": "array",
            "items": CREATE_PROPERTY_OUTPUT_SCHEMA,
        },
    },
    "required": [
        "requested_count",
        "processed_count",
        "created_count",
        "updated_existing_count",
        "results",
    ],
}

EDIT_PROPERTY_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "updated": {"type": "boolean"},
        "property_id": {"type": "integer"},
        "internal_name": {"type": ["string", "null"]},
        "name": {"type": "string"},
        "type": {
            "type": "string",
            "enum": PROPERTY_TYPE_ENUM,
        },
        "type_label": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["updated", "property_id", "internal_name", "name", "type", "type_label", "message"],
}

EDIT_PROPERTIES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "requested_count": {"type": "integer"},
        "processed_count": {"type": "integer"},
        "updated_count": {"type": "integer"},
        "results": {
            "type": "array",
            "items": EDIT_PROPERTY_OUTPUT_SCHEMA,
        },
    },
    "required": ["requested_count", "processed_count", "updated_count", "results"],
}

GET_COMPANY_LANGUAGES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "default_language_code": {"type": "string"},
        "enabled_languages": {
            "type": "array",
            "items": COMPANY_LANGUAGE_OUTPUT_SCHEMA,
        },
    },
    "required": ["default_language_code", "enabled_languages"],
}

CREATE_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "created": {"type": "boolean"},
        "select_value_id": {"type": "integer"},
        "property_id": {"type": "integer"},
        "value": {"type": "string"},
        "full_value_name": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["created", "select_value_id", "property_id", "value", "full_value_name", "message"],
}

CREATE_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "requested_count": {"type": "integer"},
        "processed_count": {"type": "integer"},
        "created_count": {"type": "integer"},
        "updated_existing_count": {"type": "integer"},
        "results": {
            "type": "array",
            "items": CREATE_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA,
        },
    },
    "required": [
        "requested_count",
        "processed_count",
        "created_count",
        "updated_existing_count",
        "results",
    ],
}

EDIT_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "updated": {"type": "boolean"},
        "select_value_id": {"type": "integer"},
        "property_id": {"type": "integer"},
        "value": {"type": "string"},
        "full_value_name": {"type": "string"},
        "message": {"type": "string"},
    },
    "required": ["updated", "select_value_id", "property_id", "value", "full_value_name", "message"],
}

EDIT_PROPERTY_SELECT_VALUES_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "requested_count": {"type": "integer"},
        "processed_count": {"type": "integer"},
        "updated_count": {"type": "integer"},
        "results": {
            "type": "array",
            "items": EDIT_PROPERTY_SELECT_VALUE_OUTPUT_SCHEMA,
        },
    },
    "required": ["requested_count", "processed_count", "updated_count", "results"],
}
