# Generated by Django 5.0.7 on 2024-07-22 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_squashed_0128_alter_multitenantuser_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='multitenantuserlogintoken',
            name='token',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
