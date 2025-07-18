# Generated by Django 5.2 on 2025-07-04 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0030_amazonremotelog'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonsaleschannel',
            name='listing_owner',
            field=models.BooleanField(default=False, help_text='Indicates if the sales channel have listing_owner status and can edit or create listings'),
        ),
    ]
