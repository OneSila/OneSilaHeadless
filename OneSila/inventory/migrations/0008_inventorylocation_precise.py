# Generated by Django 5.0.2 on 2024-05-22 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_remove_inventorylocation_parent_location_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventorylocation',
            name='precise',
            field=models.BooleanField(default=False),
        ),
    ]
