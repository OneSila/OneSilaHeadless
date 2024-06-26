# Generated by Django 5.0.2 on 2024-04-10 20:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0012_remove_address_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='email',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='language',
            field=models.CharField(choices=[('EN', 'English'), ('NL', 'Dutch'), ('RU', 'Russian'),
                                   ('DE', 'German'), ('FR', 'French')], default='EN', max_length=2),
        ),
        migrations.AddField(
            model_name='company',
            name='phone',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
