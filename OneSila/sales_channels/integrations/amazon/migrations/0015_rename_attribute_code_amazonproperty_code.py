# Generated by Django 5.2 on 2025-06-16 14:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0014_alter_amazonpublicdefinition_export_definition_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='amazonproperty',
            old_name='attribute_code',
            new_name='code',
        ),
    ]
