# Generated by Django 4.2.6 on 2023-12-15 18:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0003_alter_company_related_companies'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'verbose_name_plural': 'companies'},
        ),
        migrations.AlterModelOptions(
            name='internalcompany',
            options={'verbose_name_plural': 'interal companies'},
        ),
        migrations.AlterModelOptions(
            name='person',
            options={'verbose_name': 'person', 'verbose_name_plural': 'people'},
        ),
    ]
