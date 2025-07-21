from django.db import migrations, models


def deduplicate_internal_names(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    MultiTenantCompany = apps.get_model('core', 'MultiTenantCompany')

    for company in MultiTenantCompany.objects.all():
        seen = {}
        props = (
            Property.objects
            .filter(multi_tenant_company=company)
            .exclude(internal_name__isnull=True)
            .order_by('id')
            .values('id', 'internal_name')
        )
        for prop in props:
            name = prop['internal_name']
            if not name:
                continue
            if name not in seen:
                seen[name] = 1
                continue
            idx = seen[name]
            new_name = f"{name}_{idx}"
            while new_name in seen:
                idx += 1
                new_name = f"{name}_{idx}"
            seen[name] = idx + 1
            seen[new_name] = 1
            Property.objects.filter(pk=prop['id']).update(internal_name=new_name)


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0012_alter_property_options_and_more'),
    ]

    operations = [
        migrations.RunPython(deduplicate_internal_names, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='property',
            constraint=models.UniqueConstraint(
                fields=['multi_tenant_company', 'internal_name'],
                condition=models.Q(internal_name__isnull=False),
                name='unique_internal_name_per_company',
            ),
        ),
    ]
