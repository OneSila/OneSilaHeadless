from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('amazon', '0023_merchant_suggested_asin'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonproperty',
            name='main_code',
            field=models.CharField(blank=True, max_length=255, help_text='The main attribute code (part before "__").'),
        ),
    ]
