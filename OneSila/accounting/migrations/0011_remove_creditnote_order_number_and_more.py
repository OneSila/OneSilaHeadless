# Generated by Django 5.1.1 on 2024-11-04 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0010_creditnote_order_invoice_order'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='creditnote',
            name='order_number',
        ),
        migrations.AlterField(
            model_name='invoice',
            name='order_number',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
