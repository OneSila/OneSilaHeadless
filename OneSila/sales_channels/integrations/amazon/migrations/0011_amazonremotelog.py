from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0010_amazonproducttype_remote_name_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AmazonRemoteLog',
            fields=[
                ('remotelog_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE,
                                                       parent_link=True, primary_key=True, serialize=False,
                                                       to='sales_channels.remotelog')),
                ('submission_id', models.CharField(max_length=255, null=True, blank=True)),
                ('issues', models.JSONField(null=True, blank=True)),
                ('processing_status', models.CharField(max_length=32, null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Amazon Remote Log',
                'verbose_name_plural': 'Amazon Remote Logs',
                'ordering': ['-created_at'],
            },
            bases=('sales_channels.remotelog',),
        ),
    ]
