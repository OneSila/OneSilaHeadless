# Generated by Django 5.2 on 2025-05-08 11:10

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_multitenantcompany_ai_points_and_more'),
        ('sales_channels', '0022_alter_saleschannelview_name'),
        ('woocommerce', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WoocommerceAttribute',
            fields=[
                ('remoteproperty_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteproperty')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteproperty',),
        ),
        migrations.CreateModel(
            name='WoocommerceAttributeSelectValue',
            fields=[
                ('remotepropertyselectvalue_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remotepropertyselectvalue')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remotepropertyselectvalue',),
        ),
        migrations.CreateModel(
            name='WoocommerceProductProperty',
            fields=[
                ('remoteproductproperty_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteproductproperty')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteproductproperty',),
        ),
        migrations.AddField(
            model_name='woocommercesaleschannel',
            name='timeout',
            field=models.IntegerField(default=10, help_text='Woocommerce API Timeout'),
        ),
        migrations.CreateModel(
            name='WoocommerceBrand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('remote_id', models.CharField(blank=True, help_text='ID of the object in the remote system', max_length=255, null=True)),
                ('successfully_created', models.BooleanField(default=True, help_text='Indicates if the object was successfully created in the remote system.')),
                ('outdated', models.BooleanField(default=False, help_text='Indicates if the remote product is outdated due to an error.')),
                ('outdated_since', models.DateTimeField(blank=True, help_text='Timestamp indicating when the object became outdated.', null=True)),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('sales_channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales_channels.saleschannel')),
            ],
            options={
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
    ]
