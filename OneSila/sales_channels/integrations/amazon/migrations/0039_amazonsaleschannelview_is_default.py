from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0038_alter_amazonproducttype_unique_amazonproducttype_local_instance_sales_channel_not_null_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonsaleschannelview',
            name='is_default',
            field=models.BooleanField(default=False, help_text='Marks the default marketplace for this Amazon store.'),
        ),
    ]
