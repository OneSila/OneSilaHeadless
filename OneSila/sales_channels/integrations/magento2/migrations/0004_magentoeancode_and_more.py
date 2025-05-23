# Generated by Django 5.1.1 on 2025-03-08 11:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magento2', '0003_delete_magentocustomer'),
        ('sales_channels', '0003_remoteeancode'),
    ]

    operations = [
        migrations.CreateModel(
            name='MagentoEanCode',
            fields=[
                ('remoteeancode_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteeancode')),
            ],
            options={
                'verbose_name': 'Magento EAN Code',
                'verbose_name_plural': 'Magento EAN Codes',
            },
            bases=('sales_channels.remoteeancode',),
        ),
        migrations.AddField(
            model_name='magentosaleschannel',
            name='ean_code_attribute',
            field=models.CharField(default='ean_code', help_text='Magento attribute code for the EAN code.', max_length=64),
        ),
    ]
