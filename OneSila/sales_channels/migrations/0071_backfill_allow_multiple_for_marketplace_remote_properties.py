from django.db import migrations


def _set_allow_multiple_for_child_model(apps, *, child_app_label, child_model_name):
    RemoteProperty = apps.get_model("sales_channels", "RemoteProperty")
    ChildModel = apps.get_model(child_app_label, child_model_name)

    chunk_size = 1000
    child_ids = []

    for child_id in ChildModel.objects.values_list("id", flat=True).iterator(chunk_size=chunk_size):
        child_ids.append(child_id)
        if len(child_ids) < chunk_size:
            continue

        RemoteProperty.objects.filter(pk__in=child_ids, allow_multiple=False).update(allow_multiple=True)
        child_ids = []

    if child_ids:
        RemoteProperty.objects.filter(pk__in=child_ids, allow_multiple=False).update(allow_multiple=True)


def forwards(apps, schema_editor):
    _set_allow_multiple_for_child_model(
        apps,
        child_app_label="amazon",
        child_model_name="AmazonProperty",
    )
    _set_allow_multiple_for_child_model(
        apps,
        child_app_label="shein",
        child_model_name="SheinProperty",
    )
    _set_allow_multiple_for_child_model(
        apps,
        child_app_label="ebay",
        child_model_name="EbayProperty",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("sales_channels", "0070_alter_remotepropertyselectvalue_local_instance"),
        ("amazon", "0072_remove_amazonproperty_allows_unmapped_values"),
        ("shein", "0023_remove_sheinproperty_allows_unmapped_values"),
        ("ebay", "0026_alter_ebaypropertyselectvalue_local_instance"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
