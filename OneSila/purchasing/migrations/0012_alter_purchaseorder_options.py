# Generated by Django 5.0.2 on 2024-06-08 12:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0011_alter_purchaseorderitem_item_delete_supplierproduct'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchaseorder',
            options={'ordering': ('-created_at',)},
        ),
    ]
