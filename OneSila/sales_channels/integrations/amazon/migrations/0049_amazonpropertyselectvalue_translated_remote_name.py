from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0048_amazonproduct_last_sync_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonpropertyselectvalue',
            name='translated_remote_name',
            field=models.CharField(
                max_length=512,
                null=True,
                blank=True,
                help_text='Remote name translated into the company language.',
            ),
        ),
    ]
