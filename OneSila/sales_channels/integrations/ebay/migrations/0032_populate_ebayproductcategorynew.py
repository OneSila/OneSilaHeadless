from django.db import migrations


BATCH_SIZE = 2000


def forwards_func(apps, schema_editor):
    EbayProductCategory = apps.get_model("ebay", "EbayProductCategory")
    EbayProductCategoryNew = apps.get_model("ebay", "EbayProductCategoryNew")
    RemoteProductCategory = apps.get_model("sales_channels", "RemoteProductCategory")
    ContentType = apps.get_model("contenttypes", "ContentType")

    ebay_product_category_new_ct, _ = ContentType.objects.get_or_create(
        app_label="ebay",
        model="ebayproductcategorynew",
    )

    queryset = (
        EbayProductCategory.objects.order_by("id")
        .values(
            "id",
            "remote_id",
            "created_by_multi_tenant_user_id",
            "last_update_by_multi_tenant_user_id",
            "multi_tenant_company_id",
            "product_id",
            "sales_channel_id",
            "view_id",
        )
    )

    for row in queryset.iterator(chunk_size=BATCH_SIZE):
        instance, _ = EbayProductCategoryNew.objects.get_or_create(
            legacy_id=row["id"],
            defaults={
                "remote_id": row["remote_id"],
                "require_view": True,
                "created_by_multi_tenant_user_id": row["created_by_multi_tenant_user_id"],
                "last_update_by_multi_tenant_user_id": row["last_update_by_multi_tenant_user_id"],
                "multi_tenant_company_id": row["multi_tenant_company_id"],
                "product_id": row["product_id"],
                "sales_channel_id": row["sales_channel_id"],
                "view_id": row["view_id"],
            },
        )

        RemoteProductCategory.objects.filter(pk=instance.pk).update(
            polymorphic_ctype_id=ebay_product_category_new_ct.id,
        )

    ebay_product_category_new_ids = EbayProductCategoryNew.objects.values_list("id", flat=True)
    RemoteProductCategory.objects.filter(
        id__in=ebay_product_category_new_ids
    ).exclude(
        polymorphic_ctype_id=ebay_product_category_new_ct.id
    ).update(
        polymorphic_ctype_id=ebay_product_category_new_ct.id
    )


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("ebay", "0031_ebayproductcategorynew"),
    ]

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
