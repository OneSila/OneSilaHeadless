from django.db import migrations


BATCH_SIZE = 2000


def forwards_func(apps, schema_editor):
    AmazonProductBrowseNode = apps.get_model("amazon", "AmazonProductBrowseNode")
    AmazonProductBrowseNodeNew = apps.get_model("amazon", "AmazonProductBrowseNodeNew")
    RemoteProductCategory = apps.get_model("sales_channels", "RemoteProductCategory")
    ContentType = apps.get_model("contenttypes", "ContentType")

    amazon_product_browse_node_new_ct, _ = ContentType.objects.get_or_create(
        app_label="amazon",
        model="amazonproductbrowsenodenew",
    )

    queryset = (
        AmazonProductBrowseNode.objects.order_by("id")
        .values(
            "id",
            "created_at",
            "updated_at",
            "recommended_browse_node_id",
            "created_by_multi_tenant_user_id",
            "last_update_by_multi_tenant_user_id",
            "multi_tenant_company_id",
            "product_id",
            "sales_channel_id",
            "view_id",
        )
    )

    for row in queryset.iterator(chunk_size=BATCH_SIZE):
        instance, _ = AmazonProductBrowseNodeNew.objects.get_or_create(
            legacy_id=row["id"],
            defaults={
                "remote_id": row["recommended_browse_node_id"],
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
            polymorphic_ctype_id=amazon_product_browse_node_new_ct.id,
        )

    amazon_product_browse_node_new_ids = AmazonProductBrowseNodeNew.objects.values_list("id", flat=True)
    RemoteProductCategory.objects.filter(
        id__in=amazon_product_browse_node_new_ids
    ).exclude(
        polymorphic_ctype_id=amazon_product_browse_node_new_ct.id
    ).update(
        polymorphic_ctype_id=amazon_product_browse_node_new_ct.id
    )


class Migration(migrations.Migration):

    dependencies = [
        ("amazon", "0074_amazonproductbrowsenodenew"),
    ]

    operations = [
        migrations.RunPython(forwards_func, migrations.RunPython.noop),
    ]
