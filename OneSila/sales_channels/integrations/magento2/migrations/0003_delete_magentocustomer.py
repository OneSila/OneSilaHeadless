# Generated by Django 5.1.1 on 2025-03-07 18:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('magento2', '0002_magentosaleschannel_attribute_set_skeleton_id'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MagentoCustomer',
        ),
    ]
