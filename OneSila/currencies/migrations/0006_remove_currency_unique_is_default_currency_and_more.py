# Generated by Django 5.0.2 on 2024-06-16 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0103_alter_multitenantuser_timezone'),
        ('currencies', '0005_alter_currency_exchange_rate'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='currency',
            name='unique_is_default_currency',
        ),
        migrations.AddConstraint(
            model_name='currency',
            constraint=models.UniqueConstraint(condition=models.Q(('is_default_currency', True)), fields=(
                'multi_tenant_company',), name='unique_is_default_currency', violation_error_message='You can only have one default currency.'),
        ),
    ]
