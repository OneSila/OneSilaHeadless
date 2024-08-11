# Generated by Django 5.0.7 on 2024-08-09 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0018_delete_internalshippingaddress'),
        ('core', '0133_alter_multitenantuser_timezone'),
        ('products', '0026_auto_20240809_1303'),
        ('taxes', '0006_alter_vatrate_name'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('type', models.Value('SUPPLIER')), _negated=True), ('sku__isnull', False), _connector='OR'), name='sku_required_for_supplier_product', violation_error_message='Supplier products require an sku'),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('type', models.Value('SUPPLIER')), _negated=True), ('supplier__isnull', False), _connector='OR'), name='supplier_required_for_supplier_product', violation_error_message='Supplier products require a Supplier'),
        ),
    ]