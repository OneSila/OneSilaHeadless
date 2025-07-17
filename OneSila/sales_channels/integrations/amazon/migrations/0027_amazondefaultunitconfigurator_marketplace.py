from django.db import migrations, models
import django.db.models.deletion


def delete_configurators(apps, schema_editor):
    AmazonDefaultUnitConfigurator = apps.get_model('amazon', 'AmazonDefaultUnitConfigurator')
    AmazonDefaultUnitConfigurator.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0026_alter_amazonproperty_main_code_and_more'),
    ]

    operations = [
        migrations.RunPython(delete_configurators, migrations.RunPython.noop),
        migrations.AddField(
            model_name='amazondefaultunitconfigurator',
            name='marketplace',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                help_text='The Amazon marketplace for this value.',
                to='amazon.amazonsaleschannelview',
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='amazondefaultunitconfigurator',
            unique_together={('sales_channel', 'marketplace', 'code')},
        ),
    ]
