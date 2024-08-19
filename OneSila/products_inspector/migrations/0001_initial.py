# Generated by Django 5.0.7 on 2024-08-09 20:52

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0133_alter_multitenantuser_timezone'),
        ('products', '0027_product_sku_required_for_supplier_product_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Inspector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('has_missing_information', models.BooleanField(default=False)),
                ('has_missing_optional_information', models.BooleanField(default=False)),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='inspector', to='products.product')),
            ],
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='InspectorBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Sort Order')),
                ('simple_product_applicability', models.CharField(choices=[('REQUIRED', 'Required'), ('OPTIONAL', 'Optional'), ('NONE', 'None')], default='NONE', max_length=10)),
                ('configurable_product_applicability', models.CharField(choices=[('REQUIRED', 'Required'), ('OPTIONAL', 'Optional'), ('NONE', 'None')], default='NONE', max_length=10)),
                ('manufacturable_product_applicability', models.CharField(choices=[('REQUIRED', 'Required'), ('OPTIONAL', 'Optional'), ('NONE', 'None')], default='NONE', max_length=10)),
                ('bundle_product_applicability', models.CharField(choices=[('REQUIRED', 'Required'), ('OPTIONAL', 'Optional'), ('NONE', 'None')], default='NONE', max_length=10)),
                ('dropship_product_applicability', models.CharField(choices=[('REQUIRED', 'Required'), ('OPTIONAL', 'Optional'), ('NONE', 'None')], default='NONE', max_length=10)),
                ('supplier_product_applicability', models.CharField(choices=[('REQUIRED', 'Required'), ('OPTIONAL', 'Optional'), ('NONE', 'None')], default='NONE', max_length=10)),
                ('error_code', models.IntegerField(choices=[(101, 'Product is missing required images')])),
                ('successfully_checked', models.BooleanField(default=False)),
                ('inspector', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='products_inspector.inspector')),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
            ],
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='InspectorBlockHasImages',
            fields=[
            ],
            options={
                'verbose_name': 'Inspector Block Has Images',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('products_inspector.inspectorblock',),
        ),
        migrations.AddIndex(
            model_name='inspector',
            index=models.Index(fields=['product'], name='products_in_product_b90206_idx'),
        ),
        migrations.AddIndex(
            model_name='inspectorblock',
            index=models.Index(fields=['inspector'], name='products_in_inspect_6eba5e_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='inspectorblock',
            unique_together={('inspector', 'error_code')},
        ),
    ]