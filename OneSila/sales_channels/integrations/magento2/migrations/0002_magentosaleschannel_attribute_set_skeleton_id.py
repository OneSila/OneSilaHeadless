# Generated by Django 5.1.1 on 2025-03-07 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('magento2', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='magentosaleschannel',
            name='attribute_set_skeleton_id',
            field=models.PositiveIntegerField(default=4, help_text='Default skeleton ID used for attribute set creation during initial import.'),
        ),
    ]
