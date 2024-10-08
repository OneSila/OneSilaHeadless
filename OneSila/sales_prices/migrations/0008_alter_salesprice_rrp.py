# Generated by Django 5.0.7 on 2024-07-21 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales_prices', '0007_rename_discount_amount_salesprice_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesprice',
            name='rrp',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Reccomended Retail Price'),
        ),
    ]
