# Generated by Django 5.0.7 on 2024-08-10 14:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0030_merge_20240809_2103'),
    ]

    operations = [
        migrations.RenameModel('UmbrellaProduct', 'ConfigurableProduct')
    ]
