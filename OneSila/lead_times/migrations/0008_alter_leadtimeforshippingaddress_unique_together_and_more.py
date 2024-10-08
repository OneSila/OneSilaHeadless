# Generated by Django 5.0.7 on 2024-07-31 12:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0016_company_currency'),
        ('core', '0133_alter_multitenantuser_timezone'),
        ('lead_times', '0007_leadtime_shippingaddresses_alter_leadtime_unit'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='leadtimeforshippingaddress',
            unique_together={('multi_tenant_company', 'shippingaddress')},
        ),
        migrations.DeleteModel(
            name='LeadTimeTranslation',
        ),
    ]
