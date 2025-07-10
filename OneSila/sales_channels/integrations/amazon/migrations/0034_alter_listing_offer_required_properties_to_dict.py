from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0033_amazonpublicdefinition_allowed_in_listing_offer_request'),
    ]

    operations = [
        migrations.AlterField(
            model_name='amazonproducttype',
            name='listing_offer_required_properties',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
