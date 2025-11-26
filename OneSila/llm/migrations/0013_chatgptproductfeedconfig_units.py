from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("llm", "0012_chatgptproductfeedconfig_mpn_property"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatgptproductfeedconfig",
            name="length_unit",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="chatgptproductfeedconfig",
            name="weight_unit",
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
