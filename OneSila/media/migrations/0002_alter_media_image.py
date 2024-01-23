# Generated by Django 4.2.6 on 2024-01-02 11:06

import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='media',
            name='image',
            field=models.ImageField(upload_to='images/', validators=[core.validators.validate_image_extension,
                                    core.validators.no_dots_in_filename], verbose_name='Image (High resolution)'),
        ),
    ]
