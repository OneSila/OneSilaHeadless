# Generated by Django 5.0.2 on 2024-05-28 20:01

import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0004_media_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/',
                                    validators=[core.validators.validate_image_extension], verbose_name='Image (High resolution)'),
        ),
    ]
