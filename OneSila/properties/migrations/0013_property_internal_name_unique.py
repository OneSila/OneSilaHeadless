from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0012_alter_property_options_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='property',
            constraint=models.UniqueConstraint(
                fields=['multi_tenant_company', 'internal_name'],
                name='uniq_internal_name_per_company',
            ),
        ),
    ]
