# Generated by Django 5.1.1 on 2024-09-12 15:14

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0021_alter_company_unique_together'),
        ('core', '0134_demodatarelation_created_by_multi_tenant_user_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'ordering': ('-is_default_invoice_address',), 'verbose_name_plural': 'addresses'},
        ),
        migrations.RemoveConstraint(
            model_name='address',
            name='unique_invoice_address_per_company',
        ),
        migrations.AddField(
            model_name='address',
            name='is_default_invoice_address',
            field=models.BooleanField(default=False),
        ),
        migrations.AddConstraint(
            model_name='address',
            constraint=models.UniqueConstraint(condition=models.Q(('is_default_invoice_address', True), ('is_invoice_address', True)), fields=('company', 'is_default_invoice_address'), name='unique_default_invoice_address_per_company', violation_error_message='Company already has a default invoice address.'),
        ),
    ]
