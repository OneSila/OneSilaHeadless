# Generated by Django 5.0.7 on 2024-08-04 21:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0026_rename_umbrella_bundlevariation_parent_and_more'),
    ]

    operations = [
        migrations.RenameModel('UmbrellaVariation', 'ConfigurableVariation')
    ]