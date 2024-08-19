# Generated by Django 5.0.7 on 2024-08-04 21:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0027_auto_20240804_2234'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='umbrella_variations',
            new_name='configurable_variations',
        ),
        migrations.AlterField(
            model_name='configurablevariation',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ConfigurableVariation_umbrellas', to='products.product'),
        ),
        migrations.AlterField(
            model_name='configurablevariation',
            name='variation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ConfigurableVariation_variations', to='products.product'),
        ),
    ]