# Generated by Django 5.0.2 on 2024-07-18 14:40

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0121_alter_multitenantuser_timezone'),
        ('properties', '0006_alter_propertyselectvaluetranslation_language_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductPropertyTextTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('language', models.CharField(choices=[('nl', 'Nederlands'), ('en', 'English')], default='en', max_length=7)),
                ('value_text', models.CharField(blank=True, max_length=255, null=True, verbose_name='Text')),
                ('value_description', models.TextField(blank=True, null=True, verbose_name='Description')),
            ],
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.RemoveField(
            model_name='productproperty',
            name='value_string',
        ),
        migrations.RemoveField(
            model_name='productproperty',
            name='value_text',
        ),
        migrations.AddField(
            model_name='property',
            name='is_product_type',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='property',
            name='type',
            field=models.CharField(choices=[('INT', 'Integer'), ('FLOAT', 'Float'), ('TEXT', 'Text'), ('DESCRIPTION', 'Description'), ('BOOLEAN',
                                   'Boolean'), ('DATE', 'Date'), ('DATETIME', 'Date time')], db_index=True, max_length=20, verbose_name='Type of property'),
        ),
        migrations.AlterUniqueTogether(
            name='propertyselectvaluetranslation',
            unique_together={('value', 'language', 'multi_tenant_company')},
        ),
        migrations.AlterUniqueTogether(
            name='propertytranslation',
            unique_together={('name', 'language', 'multi_tenant_company')},
        ),
        migrations.AddConstraint(
            model_name='property',
            constraint=models.UniqueConstraint(condition=models.Q(('is_product_type', True)), fields=(
                'multi_tenant_company',), name='unique_is_product_type', violation_error_message='You can only have one product type per multi-tenant company.'),
        ),
        migrations.AddField(
            model_name='productpropertytexttranslation',
            name='multi_tenant_company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.multitenantcompany'),
        ),
        migrations.AddField(
            model_name='productpropertytexttranslation',
            name='product_property',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='properties.productproperty'),
        ),
        migrations.AlterUniqueTogether(
            name='productpropertytexttranslation',
            unique_together={('product_property', 'language')},
        ),
    ]
