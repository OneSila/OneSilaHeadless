# Generated by Django 5.1.1 on 2024-10-20 18:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0008_accountingmirrorcreditnote_outdated_and_more'),
        ('contacts', '0023_alter_address_options_and_more'),
        ('taxes', '0007_vatrate_created_by_multi_tenant_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountingmirrorcreditnote',
            name='local_instance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounting.creditnote'),
        ),
        migrations.AlterField(
            model_name='accountingmirrorcustomer',
            name='local_instance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='contacts.company'),
        ),
        migrations.AlterField(
            model_name='accountingmirrorinvoice',
            name='local_instance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounting.invoice'),
        ),
        migrations.AlterField(
            model_name='accountingmirrorvat',
            name='local_instance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taxes.vatrate'),
        ),
    ]
