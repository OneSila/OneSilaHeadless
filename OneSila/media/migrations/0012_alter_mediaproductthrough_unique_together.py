# Generated by Django 5.1.1 on 2025-02-11 11:19

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('media', '0011_remove_product_duplicate_media'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='mediaproductthrough',
            unique_together={('product', 'media')},
        ),
    ]
