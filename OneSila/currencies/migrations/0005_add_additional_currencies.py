from django.db import migrations


def add_currencies(apps, schema_editor):
    PublicCurrency = apps.get_model('currencies', 'PublicCurrency')
    from currencies.currencies import currencies as currency_dict

    for data in currency_dict.values():
        PublicCurrency.objects.get_or_create(
            iso_code=data['iso_code'],
            defaults={'name': data['name'], 'symbol': data['symbol']}
        )

class Migration(migrations.Migration):

    dependencies = [
        ('currencies', '0004_alter_publiccurrency_options'),
    ]

    operations = [
        migrations.RunPython(add_currencies, migrations.RunPython.noop),
    ]
