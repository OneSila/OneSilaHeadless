# Generated by Django 5.0.2 on 2024-03-25 13:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_bundlevariation_unique_together_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='tax_rate',
        ),
    ]