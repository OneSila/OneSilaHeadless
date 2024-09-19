# Generated by Django 5.1.1 on 2024-09-13 18:58

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0134_demodatarelation_created_by_multi_tenant_user_and_more'),
        ('sales_channels', '0012_alter_remotecurrency_unique_together_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteProductConfigurator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('remote_id', models.CharField(blank=True, help_text='ID of the object in the remote system', max_length=255, null=True)),
                ('successfully_created', models.BooleanField(default=True, help_text='Indicates if the object was successfully created in the remote system.')),
                ('outdated', models.BooleanField(default=False, help_text='Indicates if the remote product is outdated due to an error.')),
                ('outdated_since', models.DateTimeField(blank=True, help_text='Timestamp indicating when the object became outdated.', null=True)),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
                ('remote_product', models.ForeignKey(help_text='The remote product associated with this configurator.', on_delete=django.db.models.deletion.CASCADE, to='sales_channels.remoteproduct')),
                ('remote_properties', models.ManyToManyField(help_text='The remote properties associated with this configurator.', related_name='configurators', to='sales_channels.remoteproperty')),
                ('sales_channel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sales_channels.saleschannel')),
            ],
            options={
                'verbose_name': 'Remote Product Configurator',
                'verbose_name_plural': 'Remote Product Configurators',
                'unique_together': {('remote_product',)},
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
    ]
