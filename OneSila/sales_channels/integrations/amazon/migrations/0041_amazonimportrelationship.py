from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('amazon', '0040_gtin_exemption_property'),
        ('imports_exports', '0013_import_async_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AmazonImportRelationship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent_sku', models.CharField(max_length=255)),
                ('child_sku', models.CharField(max_length=255)),
                ('import_process', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='amazon_relationships', to='imports_exports.import')),
            ],
            options={
                'verbose_name': 'Amazon Import Relationship',
                'verbose_name_plural': 'Amazon Import Relationships',
                'unique_together': {('import_process', 'parent_sku', 'child_sku')},
            },
        ),
    ]

