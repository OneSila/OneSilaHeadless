# Generated by Django 5.2 on 2025-06-19 09:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0006_alter_integrationtaskqueue_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='integration',
            name='hostname',
            field=models.CharField(help_text='Hostname or identifier for the integration (e.g. domain name or marketplace slug)', max_length=255, validators=[django.core.validators.RegexValidator(message='Enter a valid hostname (e.g., example.com)', regex='^([a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,}$')]),
        ),
    ]
