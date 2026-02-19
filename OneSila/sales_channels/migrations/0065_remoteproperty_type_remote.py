from django.db import migrations, models
from django.db.models import Case, CharField, F, Value, When


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
        type_remote__isnull=True,
    ).update(
        type_remote=Case(
            *cases,
            output_field=CharField(max_length=16),
        )
    )


def forwards(apps, schema_editor):
    RemoteProperty = apps.get_model("sales_channels", "RemoteProperty")

    # Prefer values already preserved in original_type.
    RemoteProperty.objects.filter(
        type_remote__isnull=True,
        original_type__isnull=False,
    ).update(type_remote=F("original_type"))

    # Fallback to current integration-specific type for legacy rows where original_type is missing.
    _backfill_from_child_model(apps, child_app_label="amazon", child_model_name="AmazonProperty")
    _backfill_from_child_model(apps, child_app_label="ebay", child_model_name="EbayProperty")
    _backfill_from_child_model(apps, child_app_label="shein", child_model_name="SheinProperty")


def backwards(apps, schema_editor):
    RemoteProperty = apps.get_model("sales_channels", "RemoteProperty")
    RemoteProperty.objects.update(type_remote=None)


class Migration(migrations.Migration):

    dependencies = [
        ("sales_channels", "0064_backfill_remoteproperty_original_type"),
        ("amazon", "0070_amazonpropertyselectvalue_bool_value"),
        ("ebay", "0023_ebaypropertyselectvalue_bool_value"),
        ("shein", "0021_sheinproductcategory_shein_shein_product_3d4ff6_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="remoteproperty",
            name="type_remote",
            field=models.CharField(
                blank=True,
                choices=[
                    ("INT", "Integer"),
                    ("FLOAT", "Float"),
                    ("TEXT", "Text"),
                    ("DESCRIPTION", "Description"),
                    ("BOOLEAN", "Boolean"),
                    ("DATE", "Date"),
                    ("DATETIME", "Date time"),
                    ("SELECT", "Select"),
                    ("MULTISELECT", "Multi Select"),
                ],
                help_text="Remote property type stored on the base RemoteProperty model.",
                max_length=16,
                null=True,
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
