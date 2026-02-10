from django.db import migrations
from django.db.models import Case, CharField, Value, When


def _backfill_from_child_model(apps, *, child_app_label, child_model_name):
    RemoteProperty = apps.get_model("sales_channels", "RemoteProperty")
    ChildModel = apps.get_model(child_app_label, child_model_name)

    chunk_size = 500
    pending = []

    for property_id, property_type in ChildModel.objects.values_list("id", "type").iterator(chunk_size=chunk_size):
        if not property_type:
            continue

        pending.append((property_id, property_type))
        if len(pending) < chunk_size:
            continue

        _apply_chunk_update(RemoteProperty, rows=pending)
        pending = []

    if pending:
        _apply_chunk_update(RemoteProperty, rows=pending)


def _apply_chunk_update(RemoteProperty, *, rows):
    ids = [property_id for property_id, _ in rows]
    cases = [When(pk=property_id, then=Value(property_type)) for property_id, property_type in rows]

    RemoteProperty.objects.filter(
        pk__in=ids,
        original_type__isnull=True,
    ).update(
        original_type=Case(
            *cases,
            output_field=CharField(max_length=16),
        )
    )


def forwards(apps, schema_editor):
    _backfill_from_child_model(apps, child_app_label="amazon", child_model_name="AmazonProperty")
    _backfill_from_child_model(apps, child_app_label="ebay", child_model_name="EbayProperty")
    _backfill_from_child_model(apps, child_app_label="shein", child_model_name="SheinProperty")


def backwards(apps, schema_editor):
    RemoteProperty = apps.get_model("sales_channels", "RemoteProperty")
    AmazonProperty = apps.get_model("amazon", "AmazonProperty")
    EbayProperty = apps.get_model("ebay", "EbayProperty")
    SheinProperty = apps.get_model("shein", "SheinProperty")

    remote_property_ids = list(
        AmazonProperty.objects.values_list("id", flat=True)
    ) + list(
        EbayProperty.objects.values_list("id", flat=True)
    ) + list(
        SheinProperty.objects.values_list("id", flat=True)
    )

    if remote_property_ids:
        RemoteProperty.objects.filter(pk__in=remote_property_ids).update(original_type=None)


class Migration(migrations.Migration):

    dependencies = [
        ("sales_channels", "0063_remoteproperty_no_text_value_and_more"),
        ("amazon", "0070_amazonpropertyselectvalue_bool_value"),
        ("ebay", "0023_ebaypropertyselectvalue_bool_value"),
        ("shein", "0021_sheinproductcategory_shein_shein_product_3d4ff6_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
