# Generated by Django 5.0.7 on 2024-08-08 07:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0018_delete_internalshippingaddress'),
        ('inventory', '0014_auto_20240808_0839'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorylocation',
            name='shippingaddress',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contacts.inventoryshippingaddress'),
        ),
    ]