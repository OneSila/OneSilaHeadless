from django.db import migrations

def populate_internal_company(apps, schema_editor):
    Integration = apps.get_model('integrations', 'Integration')
    Company = apps.get_model('contacts', 'Company')

    for integration in Integration.objects.all().iterator():
        internal_company = Company.objects.filter(multi_tenant_company=integration.multi_tenant_company).first()
        if internal_company:
            integration.internal_company = internal_company
            integration.save()
        else:
            integration.delete()

def reverse_populate_internal_company(apps, schema_editor):
    Integration = apps.get_model('integrations', 'Integration')
    Integration.objects.update(internal_company=None)

class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0006_integration_internal_company'),
    ]

    operations = [
        migrations.RunPython(populate_internal_company, reverse_populate_internal_company),
    ]
