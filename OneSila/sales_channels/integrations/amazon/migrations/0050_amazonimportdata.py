from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0049_amazonpropertyselectvalue_translated_remote_name'),
        ('products', '0019_alter_producttranslation_unique_together_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AmazonImportData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.JSONField(blank=True, default=dict)),
                ('product', models.ForeignKey(on_delete=models.CASCADE, related_name='amazon_import_data', to='products.product')),
                ('sales_channel', models.ForeignKey(on_delete=models.CASCADE, related_name='import_data', to='amazon.amazonsaleschannel')),
                ('view', models.ForeignKey(on_delete=models.CASCADE, related_name='import_data', to='amazon.amazonsaleschannelview')),
            ],
            options={
                'verbose_name': 'Amazon Import Data',
                'verbose_name_plural': 'Amazon Import Data',
                'unique_together': {('sales_channel', 'product', 'view')},
            },
        ),
    ]
