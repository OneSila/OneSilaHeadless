# Generated by Django 4.2.9 on 2024-02-20 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttranslation',
            name='url_key',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
