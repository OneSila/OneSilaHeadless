from django.db import migrations


def _populate_configs(*, apps):
    config_model = apps.get_model("llm", "ChatGptProductFeedConfig")
    company_model = apps.get_model("core", "MultiTenantCompany")

    existing_company_ids = set(
        config_model.objects.exclude(multi_tenant_company_id__isnull=True)
        .values_list("multi_tenant_company_id", flat=True)
    )

    missing_company_ids = (
        company_model.objects.exclude(id__in=existing_company_ids)
        .values_list("id", flat=True)
    )

    new_configs = [
        config_model(multi_tenant_company_id=company_id)
        for company_id in missing_company_ids
    ]

    if new_configs:
        config_model.objects.bulk_create(new_configs, batch_size=100)


def populate_configs(apps, schema_editor):
    _populate_configs(apps=apps)


class Migration(migrations.Migration):

    dependencies = [
        ("llm", "0010_chatgptproductfeedconfig"),
    ]

    operations = [
        migrations.RunPython(populate_configs, migrations.RunPython.noop),
    ]
