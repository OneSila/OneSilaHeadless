# Generated by Django 5.0.7 on 2024-07-30 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0016_company_currency'),
        ('lead_times', '0006_alter_leadtime_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadtime',
            name='shippingaddresses',
            field=models.ManyToManyField(blank=True, related_name='leadtimes', through='lead_times.LeadTimeForShippingAddress', to='contacts.shippingaddress'),
        ),
        migrations.AlterField(
            model_name='leadtime',
            name='unit',
            field=models.IntegerField(choices=[(1, 'Hour'), (2, 'Day'), (3, 'Week'), (4, 'Month')]),
        ),
    ]