# Generated by Django 5.0.2 on 2024-07-16 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0119_alter_multitenantuser_timezone'),
        ('eancodes', '0006_remove_eancode_ean_code_or_inherit_from_not_null_and_more'),
        ('products', '0024_remove_product_base_product_product_base_products'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='eancode',
            unique_together={('product', 'ean_code', 'inherit_to')},
        ),
        migrations.AddConstraint(
            model_name='eancode',
            constraint=models.UniqueConstraint(condition=models.Q(('ean_code__isnull', False)), fields=(
                'multi_tenant_company', 'ean_code'), name='unique_ean_code_per_tenant', violation_error_message='Ean code already exists'),
        ),
        migrations.AddConstraint(
            model_name='eancode',
            constraint=models.CheckConstraint(check=models.Q(('ean_code__isnull', False), ('product__isnull', False),
                                              ('inherit_to__isnull', False), _connector='OR'), name='ean_code_or_product_to_not_null'),
        ),
    ]
