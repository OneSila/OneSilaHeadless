from types import SimpleNamespace

from imports_exports.models import Import
from sales_channels.integrations.amazon.factories.imports.products_imports import AmazonProductItemFactory
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.helpers import serialize_listing_item
from spapi.rest import ApiException


class AmazonProductImportFactory(GetAmazonAPIMixin):
    """Refresh a single Amazon product by pulling listing data and processing it."""

    def __init__(self, *, product, view):
        self.product = product
        self.view = view

        channel = view.sales_channel
        if hasattr(channel, "get_real_instance"):
            channel = channel.get_real_instance()
        self.sales_channel = channel

        if self.sales_channel.multi_tenant_company_id != self.product.multi_tenant_company_id:
            raise ValueError("Marketplace view does not belong to the product multi-tenant company.")

    def _create_import_process(self):
        identifier = self.product.sku or self.product.id

        return SimpleNamespace(
            multi_tenant_company=self.product.multi_tenant_company,
            name=f"Manual Amazon product refresh - {identifier}",
            status=Import.STATUS_PROCESSING,
            percentage=0,
            broken_records=[],
            save=lambda *args, **kwargs: None,
            create_only=False,
            update_only=False,
            id=None,
        )

    def _get_listing_payload(self):
        from sales_channels.integrations.amazon.models import AmazonProduct

        remote_product = AmazonProduct.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        ).only("remote_sku").first()

        sku = remote_product.remote_sku if remote_product and remote_product.remote_sku else self.product.sku
        if not sku:
            raise ValueError("Cannot refresh Amazon product without a SKU.")

        try:
            return self.get_listing_item(
                sku=sku,
                marketplace_id=self.view.remote_id,
                included_data=[
                    "productTypes",
                    "relationships",
                    "summaries",
                    "issues",
                    "attributes",
                    "offers",
                ],
            )
        except ApiException as exc:
            if getattr(exc, "status", None) == 404:
                return None
            raise

    def run(self):
        listing = self._get_listing_payload()
        if listing is None:
            raise ValueError("Amazon listing was not found on the marketplace.")

        product_data = serialize_listing_item(listing)
        import_process = self._create_import_process()

        try:
            factory = AmazonProductItemFactory(
                product_data=product_data,
                import_process=import_process,
                sales_channel=self.sales_channel,
                is_last=False,
                updated_with=None,
            )
            factory.run()
        except Exception:
            import_process.status = Import.STATUS_FAILED
            import_process.percentage = 100
            import_process.save(update_fields=["status", "percentage"])
            raise

        return import_process
