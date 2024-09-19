# Generated by Django 5.1.1 on 2024-09-17 23:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales_channels', '0016_alter_remoteinventory_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='remoteinventory',
            name='remote_product',
            field=models.OneToOneField(default=1, help_text='The remote product associated with this inventory.', on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to='sales_channels.remoteproduct'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='remoteprice',
            name='remote_product',
            field=models.OneToOneField(default=1, help_text='The remote product associated with this price.', on_delete=django.db.models.deletion.CASCADE, related_name='price', to='sales_channels.remoteproduct'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='remoteproductcontent',
            name='remote_product',
            field=models.OneToOneField(default=1, help_text='The remote product associated with this content.', on_delete=django.db.models.deletion.CASCADE, related_name='content', to='sales_channels.remoteproduct'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='remoteinventory',
            unique_together={('remote_product',)},
        ),
        migrations.AlterUniqueTogether(
            name='remoteprice',
            unique_together={('remote_product',)},
        ),
        migrations.AlterUniqueTogether(
            name='remoteproductcontent',
            unique_together={('remote_product',)},
        ),
    ]
