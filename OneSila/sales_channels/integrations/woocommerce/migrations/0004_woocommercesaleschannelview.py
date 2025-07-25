# Generated by Django 5.2 on 2025-05-08 13:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales_channels', '0022_alter_saleschannelview_name'),
        ('woocommerce', '0003_rename_woocommerceattribute_woocommerceglobalattribute_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WoocommerceSalesChannelView',
            fields=[
                ('saleschannelview_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.saleschannelview')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.saleschannelview',),
        ),
    ]
