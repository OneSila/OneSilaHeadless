BASE_CONTENT_FIELD_FLAGS = {
    "name": True,
    "subtitle": False,
    "urlKey": True,
    "shortDescription": True,
    "description": True,
    "bulletPoints": False,
}

BASE_CONTENT_FIELD_LIMITS = {
    "name": {"min": 0, "max": 512},
    "subtitle": {"min": 0, "max": 0},
    "shortDescription": {"min": 0, "max": 500},
    "description": {"min": 0, "max": 6000},
    "bulletPoints": {"min": 0, "max": 255},
}

CONTENT_INTEGRATION_RULES = {
    "magento": {
        "flags": {},
        "limits": {"name": {"max": 255}},
    },
    "woocommerce": {
        "flags": {},
        "limits": {},
    },
    "shopify": {
        "flags": {"shortDescription": False},
        "limits": {"name": {"max": 70}, "description": {"max": 5000}},
    },
    "amazon": {
        "flags": {"shortDescription": False, "bulletPoints": True},
        "limits": {"name": {"min": 150, "max": 200}, "description": {"min": 1000, "max": 2000}},
    },
    "ebay": {
        "flags": {"subtitle": True},
        "limits": {"name": {"max": 80}, "subtitle": {"max": 55}, "description": {"max": 4000}},
    },
    "mirakl": {
        "flags": {"subtitle": True, "bulletPoints": True},
        "limits": {},
    },
    "shein": {
        "flags": {"subtitle": False, "shortDescription": False, "bulletPoints": False},
        "limits": {"name": {"max": 1000}, "description": {"max": 5000}},
    },
    "default": {"flags": {}, "limits": {}},
}
