# Generated by Django 5.2 on 2025-04-11 13:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magento2', '0010_alter_magentocurrency_store_view_code_and_more'),
        ('sales_channels', '0020_alter_remotelanguage_local_instance'),
    ]

    operations = [
        migrations.CreateModel(
            name='MagentoTaxClass',
            fields=[
                ('remotevat_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remotevat')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remotevat',),
        ),
    ]
