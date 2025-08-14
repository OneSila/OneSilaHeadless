from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0050_amazonimportdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='amazonproductproperty',
            name='remote_select_value',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='product_properties', to='amazon.amazonpropertyselectvalue'),
        ),
        migrations.AddField(
            model_name='amazonproductproperty',
            name='remote_select_values',
            field=models.ManyToManyField(blank=True, related_name='product_properties_multi', to='amazon.amazonpropertyselectvalue'),
        ),
    ]
