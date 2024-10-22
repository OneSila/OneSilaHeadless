# Generated by Django 5.1.1 on 2024-10-17 09:57

import django.db.models.deletion
from django.db import migrations, models

def set_integration_ptr(apps, schema_editor):
    SalesChannel = apps.get_model('sales_channels', 'SalesChannel')
    Integration = apps.get_model('integrations', 'Integration')

    i = 1
    for sales_channel in SalesChannel.objects.all():
        # If no matching Integration exists, create one
        integration = Integration.objects.create(
            id=sales_channel.id,
            hostname=f'examplhostname {i}',
        )

        sales_channel.integration_ptr_id = integration.id
        sales_channel.save(update_fields=['integration_ptr_id'])
        i = i + 1


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0001_initial'),
        ('sales_channels', '0030_alter_saleschannel_unique_together_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saleschannel',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='saleschannel',
            name='created_by_multi_tenant_user',
        ),
        migrations.RemoveField(
            model_name='saleschannel',
            name='last_update_by_multi_tenant_user',
        ),
        migrations.RemoveField(
            model_name='saleschannel',
            name='multi_tenant_company',
        ),
        migrations.RemoveField(
            model_name='saleschannel',
            name='polymorphic_ctype',
        ),
        migrations.RemoveField(
            model_name='saleschannel',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='saleschannel',
            name='integration_ptr',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to='integrations.Integration',
                null=True,
                blank=True,
            ),
        ),
        migrations.RunPython(set_integration_ptr, migrations.RunPython.noop),
    ]
