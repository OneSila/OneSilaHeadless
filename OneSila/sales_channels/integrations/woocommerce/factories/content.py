import json

from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.woocommerce.factories.mixins import GetWoocommerceAPIMixin
from sales_channels.integrations.woocommerce.models import WoocommerceProductContent
from .mixins import WoocommerceProductTypeMixin, WoocommerceSalesChannelLanguageMixin, \
    SerialiserMixin


import logging
logger = logging.getLogger(__name__)


class WoocommerceProductContentUpdateFactory(WoocommerceSalesChannelLanguageMixin, SerialiserMixin, GetWoocommerceAPIMixin, WoocommerceProductTypeMixin, RemoteProductContentUpdateFactory):
    remote_model_class = WoocommerceProductContent

    fields_mapping = {
        "name": "name",
        "description": "description",
        "short_description": "short_description",
    }

    # def needs_update(self):
    #     return True

    def customize_payload(self):
        # We need to build a manual payload. For that we need:
        language = self.sales_channel_assign_language
        product = self.get_local_product()
        translation = product.translations.get(language=language)

        self.payload['name'] = translation.name
        self.payload['description'] = translation.description
        self.payload['short_description'] = translation.short_description

        logger.debug(f"{self.__class__.__name__} payload: {self.payload}")
        return self.payload

    def update_remote(self):
        if self.is_woocommerce_simple_product:
            return self.api.update_product(
                self.remote_product.remote_id,
                **self.payload
            )
        elif self.is_woocommerce_variable_product:
            return self.api.update_variable_product(
                self.remote_product.remote_parent_id,
                self.remote_product.remote_id,
                **self.payload
            )
        else:
            raise NotImplementedError("Unknown product type configuration.")
