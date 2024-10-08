# Generated by Django 5.0.7 on 2024-08-23 00:20

import core.validators
import dirtyfields.dirtyfields
import django.db.models.deletion
import order_returns.helpers
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0133_alter_multitenantuser_timezone'),
        ('order_returns', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderreturnitem',
            name='orderreturn',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='order_returns.orderreturn'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='OrderReturnAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(blank=True, null=True, upload_to=order_returns.helpers.get_orderreturn_attachment_folder_upload_path,
                 validators=[core.validators.validate_attachment_extensions, core.validators.no_dots_in_filename], verbose_name='File')),
                ('multi_tenant_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany')),
                ('orderreturn', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='order_returns.orderreturn')),
            ],
            options={
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
    ]
