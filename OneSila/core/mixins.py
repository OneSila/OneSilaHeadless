import types
from typing import Set


class TemporaryDisableInspectorSignalsMixin:
    """Mixin to temporarily disable inspector signals for a specific company.

    Usage:
        mixin = TemporaryDisableInspectorSignalsMixin()
        mixin.multi_tenant_company = <MultiTenantCompany>
        mixin.disable_inspector_signals()
        ... perform operations ...
        mixin.refresh_inspector_status()

    Note:
        This mixin patches the ``inspector_block_refresh`` signal only. Other
        helper functions such as ``recursively_check_components`` may still run
        if triggered by unrelated signals.
    """

    _original_inspector_send = None
    skipped_inspector_sku: Set[str]

    def disable_inspector_signals(self) -> None:
        """Temporarily patch the inspector signal to skip refreshes.

        Any call to ``inspector_block_refresh.send`` for products belonging to
        ``self.multi_tenant_company`` will be swallowed and the product SKU will
        be recorded in ``self.skipped_inspector_sku``.
        """
        from products_inspector.signals import inspector_block_refresh

        if self._original_inspector_send is not None:
            return

        self.skipped_inspector_sku = getattr(self, 'skipped_inspector_sku', set())
        original_send = inspector_block_refresh.send

        def patched_send(signal_self, sender, instance, **kwargs):
            inspector = instance
            product = getattr(inspector, 'product', None)
            company = getattr(product, 'multi_tenant_company', None)
            if company == self.multi_tenant_company:
                # Record the SKU so we can re-run inspection later.
                if product and product.sku:
                    self.skipped_inspector_sku.add(product.sku)
                return []
            # For other companies, behave normally.
            return original_send(sender, instance=instance, **kwargs)

        inspector_block_refresh.send = types.MethodType(patched_send, inspector_block_refresh)
        self._original_inspector_send = original_send

    def refresh_inspector_status(self) -> None:
        """Restore signals and re-run inspection for skipped products."""
        from products_inspector.signals import inspector_block_refresh
        from products_inspector.models import Inspector
        from products.models import Product

        if self._original_inspector_send is not None:
            inspector_block_refresh.send = self._original_inspector_send
            self._original_inspector_send = None

        if hasattr(self, 'skipped_inspector_sku') and self.skipped_inspector_sku:
            products = Product.objects.filter_multi_tenant(self.multi_tenant_company).filter(
                sku__in=self.skipped_inspector_sku
            )
        else:
            products = Product.objects.filter_multi_tenant(self.multi_tenant_company)

        inspectors = Inspector.objects.filter(product__in=products)
        for inspector in inspectors.iterator():
            inspector.inspect_product(run_async=False)
