# Generated by Django 5.2 on 2025-05-22 10:29

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_multitenantcompany_ai_points_and_more'),
        ('products', '0008_remove_product_alias_requires_parent'),
        ('taxes', '0002_alter_vatrate_unique_together_alter_vatrate_rate'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='product',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('alias_parent_product__isnull', False), ('type', 'ALIAS')),
                                              models.Q(('type', 'ALIAS'), _negated=True), _connector='OR'), name='alias_requires_parent'),
        ),
    ]
