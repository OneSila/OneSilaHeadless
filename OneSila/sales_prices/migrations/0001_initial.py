# Generated by Django 5.1.1 on 2025-02-25 10:57

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contacts', '0002_initial'),
        ('core', '0001_initial'),
        ('currencies', '0001_initial'),
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesPriceList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100)),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='start date')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='end date')),
                ('vat_included', models.BooleanField(default=False, verbose_name='Price list includes VAT')),
                ('auto_update_prices', models.BooleanField(default=True, verbose_name='Auto Update Price and Discount Price')),
                ('auto_add_products', models.BooleanField(default=False, verbose_name='Auto add all products')),
                ('price_change_pcnt', models.FloatField(blank=True,
                 help_text='How would you like to influence the max price?  Write 20 to increase it with 20%.  Or -20 to decrease with 20\\%', null=True)),
                ('discount_pcnt', models.FloatField(blank=True, help_text='What percentage discount would you like to apply?  For a 20\\% discount, write 20', null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='currencies.currency')),
                ('customers', models.ManyToManyField(blank=True, to='contacts.company')),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SalesPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rrp', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Reccomended Retail Price')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='currencies.currency')),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
            ],
            options={
                'constraints': [models.CheckConstraint(condition=models.Q(('rrp__gte', models.F('price'))), name='RRP cannot be less then the price'), models.CheckConstraint(condition=models.Q(('rrp__gte', '0.01')), name='RRP cannot be 0'), models.CheckConstraint(condition=models.Q(('price__gte', '0.01')), name='Price cannot be 0')],
                'unique_together': {('product', 'currency', 'multi_tenant_company')},
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='SalesPriceListItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('price_auto', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('discount_auto', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('price_override', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('discount_override', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_created_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('last_update_by_multi_tenant_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                 related_name='%(class)s_last_update_by_multi_tenant_user_set', to=settings.AUTH_USER_MODEL)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('salespricelist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales_prices.salespricelist')),
            ],
            options={
                'base_manager_name': 'objects',
                'unique_together': {('product', 'salespricelist', 'multi_tenant_company')},
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
    ]
