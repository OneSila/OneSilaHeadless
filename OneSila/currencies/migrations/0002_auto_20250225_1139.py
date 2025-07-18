# Generated by Django 5.1.1 on 2025-02-25 11:39

from django.db import migrations
from currencies.currencies import currencies


def populate_currencies(apps, schema_editor):
    PublicCurrency = apps.get_model('currencies', 'PublicCurrency')

    # currencies = {
    #     'AT': {'name': 'Euro', 'iso_code': 'EUR', 'symbol': '€'},
    #     'BG': {'name': 'Bulgarian Lev', 'iso_code': 'BGN', 'symbol': 'лв'},
    #     'HR': {'name': 'Croatian Kuna', 'iso_code': 'HRK', 'symbol': 'kn'},
    #     'CZ': {'name': 'Czech Koruna', 'iso_code': 'CZK', 'symbol': 'Kč'},
    #     'DK': {'name': 'Danish Krone', 'iso_code': 'DKK', 'symbol': 'kr'},
    #     'HU': {'name': 'Hungarian Forint', 'iso_code': 'HUF', 'symbol': 'Ft'},
    #     'PL': {'name': 'Polish Zloty', 'iso_code': 'PLN', 'symbol': 'zł'},
    #     'RO': {'name': 'Romanian Leu', 'iso_code': 'RON', 'symbol': 'lei'},
    #     'SE': {'name': 'Swedish Krona', 'iso_code': 'SEK', 'symbol': 'kr'},
    #     'TH': {'name': 'Thai Baht', 'iso_code': 'THB', 'symbol': '฿'},
    #     'GB': {'name': 'Pound Sterling', 'iso_code': 'GBP', 'symbol': '£'},
    #     'US': {'name': 'United States Dollar', 'iso_code': 'USD', 'symbol': '$'},
    #     'CA': {'name': 'Canadian Dollar', 'iso_code': 'CAD', 'symbol': '$'},
    #     'AU': {'name': 'Australian Dollar', 'iso_code': 'AUD', 'symbol': '$'},
    #     'JP': {'name': 'Japanese Yen', 'iso_code': 'JPY', 'symbol': '¥'},
    #     'CN': {'name': 'Chinese Yuan', 'iso_code': 'CNY', 'symbol': '¥'},
    #     'IN': {'name': 'Indian Rupee', 'iso_code': 'INR', 'symbol': '₹'},
    #     'BR': {'name': 'Brazilian Real', 'iso_code': 'BRL', 'symbol': 'R$'},
    #     'RU': {'name': 'Russian Ruble', 'iso_code': 'RUB', 'symbol': '₽'},
    #     'ZA': {'name': 'South African Rand', 'iso_code': 'ZAR', 'symbol': 'R'},
    #     'SA': {'name': 'Saudi Riyal', 'iso_code': 'SAR', 'symbol': 'ر.س'},
    #     'AE': {'name': 'United Arab Emirates Dirham', 'iso_code': 'AED', 'symbol': 'د.إ'},
    #     'MX': {'name': 'Mexican Peso', 'iso_code': 'MXN', 'symbol': '$'},
    # }

    for data in currencies.values():
        PublicCurrency.objects.get_or_create(**data)


class Migration(migrations.Migration):

    dependencies = [
        ('currencies', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_currencies),
    ]
