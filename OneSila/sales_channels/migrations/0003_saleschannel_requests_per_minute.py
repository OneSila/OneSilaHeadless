# Generated by Django 5.1.1 on 2024-09-08 21:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales_channels', '0002_saleschannel_verify_ssl'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleschannel',
            name='requests_per_minute',
            field=models.IntegerField(default=60),
        ),
    ]
