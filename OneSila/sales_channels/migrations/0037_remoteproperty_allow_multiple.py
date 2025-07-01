from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('sales_channels', '0036_alter_saleschannelviewassign_issues'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='remoteproperty',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='remoteproperty',
            name='allow_multiple',
            field=models.BooleanField(
                default=False,
                help_text='Set to True to allow multiple remote properties to map to the same local property.',
            ),
        ),
        migrations.AddConstraint(
            model_name='remoteproperty',
            constraint=models.UniqueConstraint(
                fields=('sales_channel', 'local_instance'),
                condition=models.Q(allow_multiple=False),
                name='uniq_remoteproperty_by_channel_local_when_not_multi',
            ),
        ),
    ]
