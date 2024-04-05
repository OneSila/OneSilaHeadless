# Generated by Django 5.0.2 on 2024-03-25 13:42

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_alter_multitenantuser_timezone'),
        ('products', '0005_remove_product_tax_rate'),
        ('taxes', '0002_tax_created_at_tax_multi_tenant_company_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='VatRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=3, null=True)),
                ('rate', models.IntegerField(help_text='VAT rate in percent.  Eg 21 for 21%')),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
            ],
            options={
                'verbose_name': 'VAT Rate',
                'verbose_name_plural': 'VAT Taxes',
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.DeleteModel(
            name='Tax',
        ),
    ]