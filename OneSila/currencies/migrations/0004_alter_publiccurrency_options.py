# Generated by Django 5.2.1 on 2025-05-24 09:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('currencies', '0003_alter_currency_round_prices_up_to'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='publiccurrency',
            options={'verbose_name_plural': 'Public Currencies'},
        ),
    ]
