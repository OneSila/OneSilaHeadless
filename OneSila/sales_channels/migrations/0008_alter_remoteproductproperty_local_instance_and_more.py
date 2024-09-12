# Generated by Django 5.1.1 on 2024-09-09 19:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0021_productpropertiesrule_created_by_multi_tenant_user_and_more'),
        ('sales_channels', '0007_alter_remotecurrency_local_instance_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='remoteproductproperty',
            name='local_instance',
            field=models.ForeignKey(help_text='The local ProductProperty instance associated with this remote property.', null=True, on_delete=django.db.models.deletion.CASCADE, to='properties.productproperty'),
        ),
        migrations.AlterField(
            model_name='remoteproperty',
            name='local_instance',
            field=models.ForeignKey(help_text='The local property associated with this remote property.', null=True, on_delete=django.db.models.deletion.CASCADE, to='properties.property'),
        ),
        migrations.AlterField(
            model_name='remotepropertyselectvalue',
            name='local_instance',
            field=models.ForeignKey(help_text='The local PropertySelectValue associated with this remote value.', null=True, on_delete=django.db.models.deletion.CASCADE, to='properties.propertyselectvalue'),
        ),
    ]
