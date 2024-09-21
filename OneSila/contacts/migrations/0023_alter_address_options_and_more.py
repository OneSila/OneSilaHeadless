# Generated by Django 5.1.1 on 2024-09-12 15:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0022_alter_address_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'verbose_name_plural': 'addresses'},
        ),
        migrations.RemoveConstraint(
            model_name='address',
            name='unique_default_invoice_address_per_company',
        ),
        migrations.RemoveField(
            model_name='address',
            name='is_default_invoice_address',
        ),
    ]