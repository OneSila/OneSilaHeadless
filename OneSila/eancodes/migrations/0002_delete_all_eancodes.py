# Generated by Django 5.0.2 on 2024-07-15 12:04

from django.db import migrations


def delete_all_eancodes(apps, schema_editor):
    EanCode = apps.get_model('eancodes', 'EanCode')
    EanCode.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('eancodes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(delete_all_eancodes),
    ]
