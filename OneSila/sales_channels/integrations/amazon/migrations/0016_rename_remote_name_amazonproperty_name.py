# Generated by Django 5.2 on 2025-06-16 14:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0015_rename_attribute_code_amazonproperty_code'),
    ]

    operations = [
        migrations.RenameField(
            model_name='amazonproperty',
            old_name='remote_name',
            new_name='name',
        ),
    ]
