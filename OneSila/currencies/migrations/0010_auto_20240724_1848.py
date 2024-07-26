# Generated by Django 5.0.7 on 2024-07-24 17:48

from django.db import migrations


def generate_initial_currencies(apps, schema_editor):
    from currencies.currencies import currencies

    PublicCurrency = apps.get_model('currencies.PublicCurrency')

    for key, item in currencies.items():
        PublicCurrency.objects.get_or_create(**item)


class Migration(migrations.Migration):

    dependencies = [
        ('currencies', '0009_currency_unique_iso_code_multi_tenant_company'),
    ]

    operations = [
        migrations.RunPython(generate_initial_currencies)
    ]