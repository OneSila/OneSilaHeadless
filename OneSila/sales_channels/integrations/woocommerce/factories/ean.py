from sales_channels.factories.products.eancodes import RemoteEanCodeUpdateFactory
from sales_channels.integrations.woocommerce.models import WoocommerceEanCode
from sales_channels.integrations.woocommerce.mixins import GetWoocommerceAPIMixin

from .mixins import SerialiserMixin
from .properties import WooCommerceProductAttributeMixin


class WooCommerceEanCodeUpdateFactory(WooCommerceProductAttributeMixin, GetWoocommerceAPIMixin, RemoteEanCodeUpdateFactory):
    # Eans are not stored remotely per se.
    # they are part of the product attribute payload as an option
    remote_model_class = WoocommerceEanCode

    def customize_payload(self):
        return self.apply_attribute_payload()

    def update_remote(self):
        return {}
        # NOTE: # Strangly enough this factory is called even if there is no eancode assigned.
        if self.is_woocommerce_variant_product:
            return self.api.update_variant(self.remote_product.remote_parent_id, self.remote_product.remote_id, **self.payload)
        elif self.is_woocommerce_simple_product or self.is_woocommerce_configurable_product:
            return self.api.update_product(self.remote_product.remote_id, **self.payload)
        else:
            raise NotImplementedError("Invalid product type")
