# Generated by Django 5.0.2 on 2024-04-10 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taxes', '0005_alter_vatrate_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vatrate',
            name='name',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]