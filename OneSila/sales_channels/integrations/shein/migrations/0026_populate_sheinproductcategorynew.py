from django.db import migrations


BATCH_SIZE = 2000


def forwards_func(apps, schema_editor):
    SheinProductCategory = apps.get_model("shein", "SheinProductCategory")
    SheinProductCategoryNew = apps.get_model("shein", "SheinProductCategoryNew")
    RemoteProductCategory = apps.get_model("sales_channels", "RemoteProductCategory")
    ContentType = apps.get_model("contenttypes", "ContentType")

    shein_product_category_new_ct = ContentType.objects.get(
        app_label="shein",
        model="sheinproductcategorynew",
    )

    queryset = (
        SheinProductCategory.objects.order_by("id")
        .values(
            "id",
            "remote_id",
            "product_type_remote_id",
            "created_by_multi_tenant_user_id",
            "last_update_by_multi_tenant_user_id",
            "multi_tenant_company_id",
            "product_id",
            "sales_channel_id",
        )
    )

    for row in queryset.iterator(chunk_size=BATCH_SIZE):
        instance, _ = SheinProductCategoryNew.objects.get_or_create(
            legacy_id=row["id"],
            defaults={
                "remote_id": row["remote_id"],
                "product_type_remote_id": row["product_type_remote_id"],
                "require_view": False,
                "created_by_multi_tenant_user_id": row["created_by_multi_tenant_user_id"],
                "last_update_by_multi_tenant_user_id": row["last_update_by_multi_tenant_user_id"],
                "multi_tenant_company_id": row["multi_tenant_company_id"],
                "product_id": row["product_id"],
                "sales_channel_id": row["sales_channel_id"],
            },
        )

        RemoteProductCategory.objects.filter(pk=instance.pk).update(
            polymorphic_ctype_id=shein_product_category_new_ct.id,
        )

    shein_product_category_new_ids = SheinProductCategoryNew.objects.values_list("id", flat=True)
    RemoteProductCategory.objects.filter(
        id__in=shein_product_category_new_ids
    ).exclude(
        polymorphic_ctype_id=shein_product_category_new_ct.id
    ).update(
        polymorphic_ctype_id=shein_product_category_new_ct.id
    )


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("shein", "0025_sheinproductcategorynew"),
    ]

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
