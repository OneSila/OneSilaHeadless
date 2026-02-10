from django.db import migrations
from django.db.models import Case, Value, When, BooleanField


def _copy_flag_from_child_model(apps, *, child_app_label, child_model_name):
    RemoteProperty = apps.get_model("sales_channels", "RemoteProperty")
    ChildModel = apps.get_model(child_app_label, child_model_name)

    chunk_size = 500
    pending = []

    for property_id, allows_unmapped_values in ChildModel.objects.values_list("id", "allows_unmapped_values").iterator(
        chunk_size=chunk_size
    ):
        pending.append((property_id, bool(allows_unmapped_values)))
        if len(pending) < chunk_size:
            continue

        _apply_chunk_update(RemoteProperty, rows=pending)
        pending = []

    if pending:
        _apply_chunk_update(RemoteProperty, rows=pending)


def _apply_chunk_update(RemoteProperty, *, rows):
    ids = [property_id for property_id, _ in rows]
    cases = [When(pk=property_id, then=Value(allows_unmapped_values)) for property_id, allows_unmapped_values in rows]

    RemoteProperty.objects.filter(pk__in=ids).update(
        allows_unmapped_values_remote=Case(
            *cases,
            output_field=BooleanField(),
        )
    )


def _set_true_for_child_model(apps, *, child_app_label, child_model_name):
    RemoteProperty = apps.get_model("sales_channels", "RemoteProperty")
    ChildModel = apps.get_model(child_app_label, child_model_name)

    ids = list(ChildModel.objects.values_list("id", flat=True))
    if ids:
        RemoteProperty.objects.filter(pk__in=ids).update(allows_unmapped_values_remote=True)


def forwards(apps, schema_editor):
    _copy_flag_from_child_model(apps, child_app_label="amazon", child_model_name="AmazonProperty")
    _copy_flag_from_child_model(apps, child_app_label="ebay", child_model_name="EbayProperty")
    _copy_flag_from_child_model(apps, child_app_label="shein", child_model_name="SheinProperty")

    _set_true_for_child_model(apps, child_app_label="magento2", child_model_name="MagentoProperty")
    _set_true_for_child_model(apps, child_app_label="woocommerce", child_model_name="WoocommerceGlobalAttribute")


class Migration(migrations.Migration):
    dependencies = [
        ("sales_channels", "0067_remoteproperty_allows_unmapped_values_remote"),
        ("amazon", "0070_amazonpropertyselectvalue_bool_value"),
        ("ebay", "0023_ebaypropertyselectvalue_bool_value"),
        ("shein", "0021_sheinproductcategory_shein_shein_product_3d4ff6_idx_and_more"),
        ("magento2", "0014_alter_magentoproductproperty_options"),
        ("woocommerce", "0015_alter_woocommercesaleschannel_options"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
