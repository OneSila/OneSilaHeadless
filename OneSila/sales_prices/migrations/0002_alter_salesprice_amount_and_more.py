# Generated by Django 4.2.6 on 2024-01-04 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales_prices', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salesprice',
            name='amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='salesprice',
            name='discount_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
