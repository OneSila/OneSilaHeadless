# Generated by Django 5.2 on 2025-04-03 17:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales_channels', '0013_saleschannel_import_orders'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='remotelanguage',
            unique_together=set(),
        ),
    ]
