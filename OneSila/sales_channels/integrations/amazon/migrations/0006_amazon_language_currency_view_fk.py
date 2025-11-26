from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0005_remove_amazoncurrency_is_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonremotelanguage',
            name='sales_channel_view',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='remote_languages',
                help_text='The marketplace associated with this remote language.',
                to='amazon.amazonsaleschannelview',
            ),
        ),
        migrations.AddField(
            model_name='amazoncurrency',
            name='sales_channel_view',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='remote_currencies',
                help_text='The marketplace associated with this remote currency.',
                to='amazon.amazonsaleschannelview',
            ),
        ),
    ]
