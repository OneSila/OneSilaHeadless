# Generated by Django 5.0.7 on 2024-07-30 09:59

from django.db import migrations


def convert_to_index(apps, schema):
    LeadTime = apps.get_model('lead_times', "LeadTime")

    LeadTime.objects.filter(unit="HOUR").update(unit=1)
    LeadTime.objects.filter(unit="DAY").update(unit=2)
    LeadTime.objects.filter(unit="WEEK").update(unit=3)
    LeadTime.objects.filter(unit="MONTH").update(unit=4)


class Migration(migrations.Migration):

    dependencies = [
        ('lead_times', '0002_leadtimeforshippingaddress'),
    ]

    operations = [
        migrations.RunPython(convert_to_index)
    ]
