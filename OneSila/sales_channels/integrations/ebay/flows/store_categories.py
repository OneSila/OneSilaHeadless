from sales_channels.integrations.ebay.models import EbayProductStoreCategory


def _get_configurable_variations(*, parent_product):
    if parent_product is None or not parent_product.is_configurable():
        return []
    return parent_product.get_configurable_variations(active_only=False)


def _upsert_store_categories_to_variations(*, instance) -> None:
    variations = _get_configurable_variations(parent_product=instance.product)
    if not variations:
        return

    for variation in variations:
        EbayProductStoreCategory.objects.update_or_create(
            product=variation,
            sales_channel=instance.sales_channel,
            defaults={
                "multi_tenant_company_id": variation.multi_tenant_company_id,
                "primary_store_category": instance.primary_store_category,
                "secondary_store_category": instance.secondary_store_category,
            },
        )


def ebay_product_store_category_create_flow(*, instance) -> None:
    _upsert_store_categories_to_variations(instance=instance)


def ebay_product_store_category_update_flow(*, instance) -> None:
    _upsert_store_categories_to_variations(instance=instance)


def ebay_product_store_category_delete_flow(*, instance) -> None:
    variations = _get_configurable_variations(parent_product=instance.product)
    if not variations:
        return

    variation_ids = [variation.id for variation in variations]
    if not variation_ids:
        return

    EbayProductStoreCategory.objects.filter(
        product_id__in=variation_ids,
        sales_channel=instance.sales_channel,
    ).delete()
