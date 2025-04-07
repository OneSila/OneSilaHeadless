# Generated by Django 5.1.1 on 2025-04-01 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magento2', '0007_alter_magentoattributesetattributeimport_remote_attribute_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='magentoattributesetattributeimport',
            name='structured_data',
            field=models.JSONField(blank=True, help_text='The structured data after processing the raw data.', null=True),
        ),
        migrations.AlterField(
            model_name='magentoattributesetimport',
            name='structured_data',
            field=models.JSONField(blank=True, help_text='The structured data after processing the raw data.', null=True),
        ),
    ]
