# Generated by Django 5.0.7 on 2024-08-09 12:03

from django.db import migrations
from django.db.models import ProtectedError, Q

def delete_non_compliant_supplier_products(apps, schema_editor):
    Product = apps.get_model('products', 'Product')

    non_compliant_products = Product.objects.filter(
        type="SUPPLIER"
    ).filter(
        Q(sku__isnull=True) | Q(supplier__isnull=True)
    )

    for product in non_compliant_products:
        try:
            product.delete()
        except ProtectedError as e:
            for protected_instance in e.protected_objects:
                delete_traversed_content_object(protected_instance)
            product.delete()


def delete_traversed_content_object(content_object):
    try:
        content_object.delete()
    except ProtectedError as e:
        for protected_instance in e.protected_objects:
            delete_traversed_content_object(protected_instance)
        content_object.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0018_delete_internalshippingaddress'),
        ('products', '0025_rename_always_on_stock_product_allow_backorder'),
    ]

    operations = [
        migrations.RunPython(delete_non_compliant_supplier_products),
    ]