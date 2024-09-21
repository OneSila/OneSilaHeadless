# Generated by Django 5.1.1 on 2024-09-18 00:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0036_billofmaterial_created_by_multi_tenant_user_and_more'),
        ('sales_channels', '0017_remoteinventory_remote_product_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saleschannelviewassign',
            name='status',
        ),
        migrations.AlterUniqueTogether(
            name='remoteproduct',
            unique_together={('sales_channel', 'local_instance', 'remote_parent_product'), ('sales_channel', 'remote_sku')},
        ),
    ]