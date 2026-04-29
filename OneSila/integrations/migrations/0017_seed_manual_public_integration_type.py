from django.db import migrations


APP_LABEL = "integrations"
DEFAULT_LANGUAGE = "en"
MANUAL_KEY = "manual"


def seed_manual_public_integration_type(apps, schema_editor):
    PublicIntegrationType = apps.get_model(APP_LABEL, "PublicIntegrationType")
    PublicIntegrationTypeTranslation = apps.get_model(APP_LABEL, "PublicIntegrationTypeTranslation")

    obj, _ = PublicIntegrationType.objects.update_or_create(
        key=MANUAL_KEY,
        defaults={
            "type": MANUAL_KEY,
            "subtype": None,
            "based_to": None,
            "category": "marketplace",
            "active": True,
            "is_beta": False,
            "supports_open_ai_product_feed": False,
            "sort_order": 8,
        },
    )

    PublicIntegrationTypeTranslation.objects.update_or_create(
        public_integration_type=obj,
        language=DEFAULT_LANGUAGE,
        defaults={
            "name": "Manual",
            "description": "Track a custom sales channel without connecting to an external platform.",
        },
    )


def unseed_manual_public_integration_type(apps, schema_editor):
    PublicIntegrationType = apps.get_model(APP_LABEL, "PublicIntegrationType")
    PublicIntegrationType.objects.filter(key=MANUAL_KEY).delete()


class Migration(migrations.Migration):
    dependencies = [
        (APP_LABEL, "0016_remove_publicissue_request_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_manual_public_integration_type, unseed_manual_public_integration_type),
    ]
