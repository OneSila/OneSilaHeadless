# Generated by Django 5.1.1 on 2025-04-01 18:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('imports_exports', '0004_alter_import_status'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='import',
            options={'ordering': ['-created_at']},
        ),
    ]
