# Generated by Django 5.1.1 on 2025-03-08 11:44

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0002_alter_multitenantuser_onboarding_status'),
        ('sales_channels', '0002_remove_saleschannel_sync_orders_after_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteEanCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('remote_id', models.CharField(blank=True, help_text='ID of the object in the remote system', max_length=255, null=True)),
                ('successfully_created', models.BooleanField(default=True, help_text='Indicates if the object was successfully created in the remote system.')),
                ('outdated', models.BooleanField(default=False, help_text='Indicates if the remote product is outdated due to an error.')),
                ('outdated_since', models.DateTimeField(blank=True, help_text='Timestamp indicating when the object became outdated.', null=True)),
                ('ean_code', models.CharField(blank=True, help_text='The EAN code value.', max_length=14, null=True)),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE,
                 related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
                ('remote_product', models.ForeignKey(help_text='The remote product associated with this EAN code.',
                 on_delete=django.db.models.deletion.CASCADE, related_name='eancode', to='sales_channels.remoteproduct')),
                ('sales_channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales_channels.saleschannel')),
            ],
            options={
                'verbose_name': 'Remote EAN Code',
                'verbose_name_plural': 'Remote EAN Codes',
                'unique_together': {('ean_code', 'remote_product')},
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
    ]
