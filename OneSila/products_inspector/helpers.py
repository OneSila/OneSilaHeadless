from products.models import Product
from products_inspector.constants import DOCUMENT_TYPES_BLOCK_ERROR_CODES
from products_inspector.signals import inspector_block_refresh


def _send_document_type_block_refresh(*, product):
    if not hasattr(product, "inspector"):
        return

    from products_inspector.factories.inspector_block import InspectorBlockCreateOrUpdateFactory

    inspector = product.inspector
    existing_codes = set(
        inspector.blocks.filter(error_code__in=DOCUMENT_TYPES_BLOCK_ERROR_CODES).values_list("error_code", flat=True)
    )

    for error_code in DOCUMENT_TYPES_BLOCK_ERROR_CODES:
        if error_code in existing_codes:
            continue
        InspectorBlockCreateOrUpdateFactory(inspector, error_code).run()

    existing_codes = set(
        inspector.blocks.filter(error_code__in=DOCUMENT_TYPES_BLOCK_ERROR_CODES).values_list("error_code", flat=True)
    )
    for error_code in existing_codes:
        inspector_block_refresh.send(
            sender=inspector.__class__,
            instance=inspector,
            error_code=error_code,
            run_async=False,
        )
def _refresh_document_type_blocks_for_products(
    *,
    product_ids,
    multi_tenant_company_id,
    run_async=False,
):
    if not product_ids:
        return

    product_ids = list(product_ids)

    if run_async:
        from products_inspector.tasks import (
            products_inspector__tasks__refresh_document_type_blocks_for_products,
        )

        products_inspector__tasks__refresh_document_type_blocks_for_products(
            multi_tenant_company_id=multi_tenant_company_id,
            product_ids=product_ids,
        )
        return

    queryset = Product.objects.filter(
        id__in=product_ids,
        multi_tenant_company_id=multi_tenant_company_id,
    )
    for product in queryset.iterator():
        _send_document_type_block_refresh(product=product)


def _normalise_category_ids(*, categories):
    if not isinstance(categories, list):
        return set()
    return {
        str(category_id).strip()
        for category_id in categories
        if str(category_id).strip()
    }
