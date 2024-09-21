# Generated by Django 5.1.1 on 2024-09-20 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales_channels', '0018_remove_saleschannelviewassign_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remoteinventory',
            name='quantity',
            field=models.IntegerField(blank=True, help_text='The quantity of the product available in the remote system.', null=True),
        ),
    ]