# Generated by Django 5.1.1 on 2024-10-21 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quickbooks', '0003_quickbooksaccount_company_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='quickbookscustomer',
            options={'verbose_name': 'QuickBooks Customer', 'verbose_name_plural': 'QuickBooks Customers'},
        ),
        migrations.AddField(
            model_name='quickbookscustomer',
            name='sync_token',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
