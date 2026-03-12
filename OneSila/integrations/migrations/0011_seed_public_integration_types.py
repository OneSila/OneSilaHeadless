from django.db import migrations

from sales_channels.integrations.mirakl.sub_type_constants import (
    DEFAULT_MIRAKL_SUB_TYPE,
    MIRAKL_SUB_TYPE_CHOICES,
)


APP_LABEL = "integrations"
DEFAULT_LANGUAGE = "en"


def build_marketplace_description(name):
    return f"{name} integration to manage your marketplace listings."


PUBLIC_INTEGRATION_TYPES = [
    {
        "key": "magento",
        "type": "magento",
        "subtype": None,
        "based_to_key": None,
        "category": "storefront",
        "active": True,
        "is_beta": False,
        "supports_open_ai_product_feed": True,
        "name": "Magento",
        "description": "Integrate with Magento to manage your online store seamlessly.",
    },
    {
        "key": "shopify",
        "type": "shopify",
        "subtype": None,
        "based_to_key": None,
        "category": "storefront",
        "active": True,
        "is_beta": False,
        "supports_open_ai_product_feed": True,
        "name": "Shopify",
        "description": "Shopify integration to manage your products in seconds.",
    },
    {
        "key": "woocommerce",
        "type": "woocommerce",
        "subtype": None,
        "based_to_key": None,
        "category": "storefront",
        "active": True,
        "is_beta": True,
        "supports_open_ai_product_feed": True,
        "name": "Woocommerce",
        "description": "WooCommerce integration to manage your products.",
    },
    {
        "key": "amazon",
        "type": "amazon",
        "subtype": None,
        "based_to_key": None,
        "category": "marketplace",
        "active": True,
        "is_beta": False,
        "supports_open_ai_product_feed": False,
        "name": "Amazon",
        "description": "Amazon integration to manage your marketplace listings.",
    },
    {
        "key": "ebay",
        "type": "ebay",
        "subtype": None,
        "based_to_key": None,
        "category": "marketplace",
        "active": True,
        "is_beta": False,
        "supports_open_ai_product_feed": False,
        "name": "Ebay",
        "description": "Ebay integration to manage your marketplace listings.",
    },
    {
        "key": "shein",
        "type": "shein",
        "subtype": None,
        "based_to_key": None,
        "category": "marketplace",
        "active": True,
        "is_beta": True,
        "supports_open_ai_product_feed": False,
        "name": "Shein",
        "description": "Shein integration to manage your marketplace listings.",
    },
    {
        "key": "mirakl",
        "type": "mirakl",
        "subtype": None,
        "based_to_key": None,
        "category": "marketplace",
        "active": True,
        "is_beta": True,
        "supports_open_ai_product_feed": False,
        "name": "Mirakl",
        "description": "Mirakl integration to connect OneSila with hundreds of marketplace channels from a single setup.",
    },
    {
        "key": "webhook",
        "type": "webhook",
        "subtype": None,
        "based_to_key": None,
        "category": "webhooks",
        "active": True,
        "is_beta": False,
        "supports_open_ai_product_feed": False,
        "name": "Webhook",
        "description": "Send events to your application via HTTP",
    },
] + [
    {
        "key": subtype,
        "type": "mirakl",
        "subtype": subtype,
        "based_to_key": DEFAULT_MIRAKL_SUB_TYPE,
        "category": "marketplace",
        "active": False,
        "is_beta": True,
        "supports_open_ai_product_feed": False,
        "name": name,
        "description": None,
    }
    for subtype, name in MIRAKL_SUB_TYPE_CHOICES
    if subtype != DEFAULT_MIRAKL_SUB_TYPE
]


def seed_public_integration_types(apps, schema_editor):
    PublicIntegrationType = apps.get_model(APP_LABEL, "PublicIntegrationType")
    PublicIntegrationTypeTranslation = apps.get_model(APP_LABEL, "PublicIntegrationTypeTranslation")

    created_by_key = {}

    for sort_order, item in enumerate(PUBLIC_INTEGRATION_TYPES, start=1):
        based_to = None
        if item["based_to_key"]:
            based_to = created_by_key[item["based_to_key"]]

        obj, _ = PublicIntegrationType.objects.update_or_create(
            key=item["key"],
            defaults={
                "type": item["type"],
                "subtype": item["subtype"],
                "based_to": based_to,
                "category": item["category"],
                "active": item["active"],
                "is_beta": item["is_beta"],
                "supports_open_ai_product_feed": item["supports_open_ai_product_feed"],
                "sort_order": sort_order,
            },
        )
        created_by_key[item["key"]] = obj

        PublicIntegrationTypeTranslation.objects.update_or_create(
            public_integration_type=obj,
            language=DEFAULT_LANGUAGE,
            defaults={
                "name": item["name"],
                "description": item["description"] or build_marketplace_description(item["name"]),
            },
        )


def unseed_public_integration_types(apps, schema_editor):
    PublicIntegrationType = apps.get_model(APP_LABEL, "PublicIntegrationType")
    PublicIntegrationType.objects.filter(
        key__in=[item["key"] for item in PUBLIC_INTEGRATION_TYPES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        (APP_LABEL, "0010_publicintegrationtype_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_public_integration_types, unseed_public_integration_types),
    ]
