# Generated by Django 5.1.1 on 2024-09-11 21:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magento2', '0007_magentoattributesetattribute_remote_property'),
        ('sales_channels', '0011_remoteorderitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='MagentoRemoteOrderItem',
            fields=[
                ('remoteorderitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteorderitem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteorderitem',),
        ),
    ]