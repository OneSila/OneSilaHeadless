import json

from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.woocommerce.factories.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceProductContent


class WoocommerceProductContentUpdateFactory(GetWoocommerceAPIMixin, RemoteProductContentUpdateFactory):
    remote_model_class = WoocommerceProductContent

    fields_mapping = {
        "name": "name",
        "description": "description",
        "short_description": "short_description",
    }

    def update_remote(self):
        if self.is_woocommerce_simple_product():
            return self.api.update_product(
                self.remote_instance.remote_id,
                **self.payload
            )
        elif self.is_woocommerce_variable_product():
            return self.api.update_variable_product(
                self.remote_instance.remote_parent_id,
                self.remote_instance.remote_id,
                **self.payload
            )
        else:
            raise NotImplementedError("Unknown product type configuration.")
