# Generated by Django 5.2 on 2025-04-17 12:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0005_alter_productpropertytexttranslation_language_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productproperty',
            name='value_select',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                    related_name='value_select_set', to='properties.propertyselectvalue'),
        ),
    ]
