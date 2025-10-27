from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("llm", "0011_populate_chatgptproductfeedconfig"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatgptproductfeedconfig",
            name="mpn_property",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name="+",
                to="properties.property",
            ),
        ),
    ]
