# Generated by Django 5.0.2 on 2024-06-12 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_alter_producttranslation_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producttranslation',
            name='language',
            field=models.CharField(choices=[('nl', 'Nederlands'), ('en', 'English')], default='en', max_length=7),
        ),
    ]
