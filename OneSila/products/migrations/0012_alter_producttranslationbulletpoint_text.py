# Generated by Django 5.2 on 2025-06-24 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_alter_producttranslationbulletpoint_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producttranslationbulletpoint',
            name='text',
            field=models.CharField(max_length=512),
        ),
    ]
