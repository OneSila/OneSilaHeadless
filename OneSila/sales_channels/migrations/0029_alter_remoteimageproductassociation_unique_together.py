# Generated by Django 5.1.1 on 2024-09-24 23:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0007_alter_mediaproductthrough_options'),
        ('sales_channels', '0028_alter_remotetaskqueue_error_history'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='remoteimageproductassociation',
            unique_together={('local_instance', 'sales_channel', 'remote_product')},
        ),
    ]
