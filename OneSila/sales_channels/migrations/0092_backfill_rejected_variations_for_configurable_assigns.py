from django.db import migrations


BATCH_SIZE = 1000


def backfill_rejected_variation_assigns(apps, schema_editor):
    SalesChannelViewAssign = apps.get_model("sales_channels", "SalesChannelViewAssign")
    RejectedSalesChannelViewAssign = apps.get_model("sales_channels", "RejectedSalesChannelViewAssign")
    ConfigurableVariation = apps.get_model("products", "ConfigurableVariation")

    parent_assigns = (
        SalesChannelViewAssign.objects.filter(product__type="CONFIGURABLE")
        .only(
            "id",
            "product_id",
            "sales_channel_view_id",
            "multi_tenant_company_id",
            "created_by_multi_tenant_user_id",
            "last_update_by_multi_tenant_user_id",
        )
    )

    to_create = []

    for parent_assign in parent_assigns.iterator():
        variation_ids = list(
            ConfigurableVariation.objects.filter(parent_id=parent_assign.product_id).values_list("variation_id", flat=True)
        )
        if not variation_ids:
            continue

        assigned_variation_ids = set(
            SalesChannelViewAssign.objects.filter(
                product_id__in=variation_ids,
                sales_channel_view_id=parent_assign.sales_channel_view_id,
            ).values_list("product_id", flat=True)
        )

        for variation_id in variation_ids:
            if variation_id in assigned_variation_ids:
                continue

            to_create.append(
                RejectedSalesChannelViewAssign(
                    product_id=variation_id,
                    sales_channel_view_id=parent_assign.sales_channel_view_id,
                    multi_tenant_company_id=parent_assign.multi_tenant_company_id,
                    created_by_multi_tenant_user_id=parent_assign.created_by_multi_tenant_user_id,
                    last_update_by_multi_tenant_user_id=parent_assign.last_update_by_multi_tenant_user_id,
                )
            )

            if len(to_create) >= BATCH_SIZE:
                RejectedSalesChannelViewAssign.objects.bulk_create(to_create, ignore_conflicts=True)
                to_create = []

    if to_create:
        RejectedSalesChannelViewAssign.objects.bulk_create(to_create, ignore_conflicts=True)


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("sales_channels", "0091_alter_saleschannelview_options"),
        ("products", "0025_alter_producttranslation_language"),
    ]

    operations = [
        migrations.RunPython(backfill_rejected_variation_assigns, noop_reverse),
    ]
