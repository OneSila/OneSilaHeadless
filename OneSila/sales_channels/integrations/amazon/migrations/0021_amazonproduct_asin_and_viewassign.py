from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0020_amazonsaleschannelimport'),
        ('sales_channels', '0032_alter_saleschannelview_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonproduct',
            name='asin',
            field=models.CharField(blank=True, help_text='ASIN identifier for the product.', max_length=32, null=True),
        ),
        migrations.CreateModel(
            name='AmazonSalesChannelViewAssign',
            fields=[
                ('saleschannelviewassign_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='sales_channels.saleschannelviewassign')),
                ('issues', models.JSONField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('sales_channels.saleschannelviewassign',),
        ),
    ]
