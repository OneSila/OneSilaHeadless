# Generated by Django 5.0.2 on 2024-06-06 13:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_alter_billofmaterial_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='product',
            unique_together=set(),
        ),
    ]
