# Generated by Django 4.2.6 on 2024-01-02 11:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0004_alter_company_options_alter_internalcompany_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'verbose_name_plural': 'addresses'},
        ),
        migrations.AlterModelOptions(
            name='invoiceaddress',
            options={'verbose_name_plural': 'invoice addresses'},
        ),
        migrations.AlterModelOptions(
            name='shippingaddress',
            options={'verbose_name_plural': 'shipping addresses'},
        ),
    ]
