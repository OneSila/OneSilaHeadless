# Generated by Django 5.0.2 on 2024-04-04 20:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_alter_product_sku_alter_product_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
    ]
