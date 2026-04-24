from products_inspector.constants import UNDECIDED_SALES_CHANNEL_VIEWS_ERROR
from products_inspector.signals import inspector_block_refresh


def refresh_undecided_sales_channel_views_block_for_product_flow(*, product) -> None:
    if not hasattr(product, "inspector"):
        return

    inspector_block_refresh.send(
        sender=product.inspector.__class__,
        instance=product.inspector,
        error_code=UNDECIDED_SALES_CHANNEL_VIEWS_ERROR,
        run_async=False,
    )


def refresh_undecided_sales_channel_views_blocks_for_company_flow(*, multi_tenant_company) -> None:
    from products.models import Product

    queryset = Product.objects.filter(
        multi_tenant_company=multi_tenant_company,
    )
    for product in queryset.iterator():
        refresh_undecided_sales_channel_views_block_for_product_flow(product=product)
