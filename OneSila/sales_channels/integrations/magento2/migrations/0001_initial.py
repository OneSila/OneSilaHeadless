# Generated by Django 5.1.1 on 2025-02-25 11:58

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0001_initial'),
        ('properties', '0001_initial'),
        ('sales_channels', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MagentoCategory',
            fields=[
                ('remotecategory_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remotecategory')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remotecategory',),
        ),
        migrations.CreateModel(
            name='MagentoCustomer',
            fields=[
                ('remotecustomer_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remotecustomer')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remotecustomer',),
        ),
        migrations.CreateModel(
            name='MagentoImageProductAssociation',
            fields=[
                ('remoteimageproductassociation_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteimageproductassociation')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteimageproductassociation',),
        ),
        migrations.CreateModel(
            name='MagentoInventory',
            fields=[
                ('remoteinventory_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteinventory')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteinventory',),
        ),
        migrations.CreateModel(
            name='MagentoOrder',
            fields=[
                ('remoteorder_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteorder')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteorder',),
        ),
        migrations.CreateModel(
            name='MagentoOrderItem',
            fields=[
                ('remoteorderitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteorderitem')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteorderitem',),
        ),
        migrations.CreateModel(
            name='MagentoPrice',
            fields=[
                ('remoteprice_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteprice')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteprice',),
        ),
        migrations.CreateModel(
            name='MagentoProduct',
            fields=[
                ('remoteproduct_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteproduct')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteproduct',),
        ),
        migrations.CreateModel(
            name='MagentoProductContent',
            fields=[
                ('remoteproductcontent_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteproductcontent')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remoteproductcontent',),
        ),
        migrations.CreateModel(
            name='MagentoProductProperty',
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
        migrations.CreateModel(
            name='MagentoProperty',
            fields=[
                ('remoteproperty_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remoteproperty')),
                ('attribute_code', models.CharField(help_text='The attribute code used in Magento for this property.', max_length=255, verbose_name='Attribute Code')),
            ],
            options={
                'verbose_name': 'Magento Property',
                'verbose_name_plural': 'Magento Properties',
            },
            bases=('sales_channels.remoteproperty',),
        ),
        migrations.CreateModel(
            name='MagentoPropertySelectValue',
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
            name='MagentoSalesChannel',
            fields=[
                ('saleschannel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.saleschannel')),
                ('host_api_username', models.CharField(blank=True, max_length=256, null=True)),
                ('host_api_key', models.CharField(max_length=256)),
                ('authentication_method', models.CharField(choices=[('TOK', 'Token Only'), ('PAS', 'Username / Password')], max_length=3)),
            ],
            options={
                'verbose_name': 'Magento Sales Channel',
                'verbose_name_plural': 'Magento Sales Channels',
            },
            bases=('sales_channels.saleschannel',),
        ),
        migrations.CreateModel(
            name='MagentoSalesChannelView',
            fields=[
                ('saleschannelview_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.saleschannelview')),
                ('code', models.CharField(help_text='Unique code for the sales channel view.', max_length=50)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.saleschannelview',),
        ),
        migrations.CreateModel(
            name='MagentoAttributeSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('remote_id', models.CharField(blank=True, help_text='ID of the object in the remote system', max_length=255, null=True)),
                ('successfully_created', models.BooleanField(default=True, help_text='Indicates if the object was successfully created in the remote system.')),
                ('outdated', models.BooleanField(default=False, help_text='Indicates if the remote product is outdated due to an error.')),
                ('outdated_since', models.DateTimeField(blank=True, help_text='Timestamp indicating when the object became outdated.', null=True)),
                ('group_remote_id', models.CharField(help_text='The remote group ID associated with this attribute set in Magento.',
                 max_length=256, null=True, verbose_name='Group Remote ID')),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('local_instance', models.ForeignKey(help_text='The local ProductPropertiesRule associated with this Magento attribute set.',
                 null=True, on_delete=django.db.models.deletion.SET_NULL, to='properties.productpropertiesrule')),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('sales_channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales_channels.saleschannel')),
            ],
            options={
                'verbose_name': 'Magento Attribute Set',
                'verbose_name_plural': 'Magento Attribute Sets',
                'unique_together': {('local_instance', 'sales_channel')},
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='MagentoAttributeSetAttribute',
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
                ('local_instance', models.ForeignKey(help_text='The local ProductPropertiesRuleItem associated with this Magento attribute.',
                 null=True, on_delete=django.db.models.deletion.SET_NULL, to='properties.productpropertiesruleitem')),
                ('magento_rule', models.ForeignKey(help_text='The Magento attribute set to which this attribute belongs.',
                 on_delete=django.db.models.deletion.CASCADE, to='magento2.magentoattributeset')),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('sales_channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales_channels.saleschannel')),
                ('remote_property', models.ForeignKey(help_text='The MagentoProperty associated with this attribute set attribute.',
                 on_delete=django.db.models.deletion.CASCADE, to='magento2.magentoproperty')),
            ],
            options={
                'verbose_name': 'Magento Attribute Set Attribute',
                'verbose_name_plural': 'Magento Attribute Set Attributes',
                'unique_together': {('local_instance', 'magento_rule')},
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='MagentoAttributeSetAttributeImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('raw_data', models.JSONField(help_text='The raw data being imported.')),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('import_process', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales_channels.importprocess')),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE,
                 related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
                ('remote_attribute', models.ForeignKey(help_text='The remote attribute associated with this import process.',
                 on_delete=django.db.models.deletion.CASCADE, to='magento2.magentoattributesetattribute')),
            ],
            options={
                'verbose_name': 'Magento Import Attribute Set Attribute',
                'verbose_name_plural': 'Magento Import Attribute Set Attributes',
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='MagentoAttributeSetImport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('raw_data', models.JSONField(help_text='The raw data being imported.')),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('import_process', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales_channels.importprocess')),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE,
                 related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
                ('remote_attribute_set', models.ForeignKey(help_text='The remote attribute set associated with this import process.',
                 on_delete=django.db.models.deletion.CASCADE, to='magento2.magentoattributeset')),
            ],
            options={
                'verbose_name': 'Magento Import Attribute Set',
                'verbose_name_plural': 'Magento Import Attribute Sets',
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='MagentoRemoteLanguage',
            fields=[
                ('remotelanguage_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remotelanguage')),
                ('sales_channel_view', models.ForeignKey(help_text='The sales channel view associated with this remote language.',
                 on_delete=django.db.models.deletion.CASCADE, related_name='remote_languages', to='magento2.magentosaleschannelview')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remotelanguage',),
        ),
        migrations.CreateModel(
            name='MagentoCurrency',
            fields=[
                ('remotecurrency_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                 parent_link=True, primary_key=True, serialize=False, to='sales_channels.remotecurrency')),
                ('sales_channel_view', models.ForeignKey(help_text='The sales channel view associated with this remote currency.',
                 on_delete=django.db.models.deletion.CASCADE, related_name='remote_currencies', to='magento2.magentosaleschannelview')),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.remotecurrency',),
        ),
    ]
