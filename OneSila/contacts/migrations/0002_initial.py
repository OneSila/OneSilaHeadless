# Generated by Django 5.1.1 on 2025-02-25 10:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contacts', '0001_initial'),
        ('core', '0001_initial'),
        ('currencies', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='created_by_multi_tenant_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='address',
            name='last_update_by_multi_tenant_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='address',
            name='multi_tenant_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany'),
        ),
        migrations.CreateModel(
            name='InternalShippingAddress',
            fields=[
            ],
            options={
                'verbose_name_plural': 'internal shipping addresses',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('contacts.address',),
        ),
        migrations.CreateModel(
            name='InventoryShippingAddress',
            fields=[
            ],
            options={
                'verbose_name_plural': 'inventory shipping addresses',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('contacts.address',),
        ),
        migrations.CreateModel(
            name='InvoiceAddress',
            fields=[
            ],
            options={
                'verbose_name_plural': 'invoice addresses',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('contacts.address',),
        ),
        migrations.CreateModel(
            name='ShippingAddress',
            fields=[
            ],
            options={
                'verbose_name_plural': 'shipping addresses',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('contacts.address',),
        ),
        migrations.AddField(
            model_name='company',
            name='created_by_multi_tenant_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='company',
            name='currency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='currencies.currency'),
        ),
        migrations.AddField(
            model_name='company',
            name='last_update_by_multi_tenant_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='company',
            name='multi_tenant_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany'),
        ),
        migrations.AddField(
            model_name='address',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contacts.company'),
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('contacts.company',),
        ),
        migrations.CreateModel(
            name='Influencer',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('contacts.company',),
        ),
        migrations.CreateModel(
            name='InternalCompany',
            fields=[
            ],
            options={
                'verbose_name_plural': 'interal companies',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('contacts.company',),
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('contacts.company',),
        ),
        migrations.AddField(
            model_name='person',
            name='company',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='contacts.company'),
        ),
        migrations.AddField(
            model_name='person',
            name='created_by_multi_tenant_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='person',
            name='last_update_by_multi_tenant_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='person',
            name='multi_tenant_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany'),
        ),
        migrations.AddField(
            model_name='address',
            name='person',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contacts.person'),
        ),
        migrations.AlterUniqueTogether(
            name='company',
            unique_together={('name', 'email', 'multi_tenant_company')},
        ),
    ]
