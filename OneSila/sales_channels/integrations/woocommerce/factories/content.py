import json

from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.woocommerce.models import WoocommerceProductContent
from .mixins import WooCommerceUpdateRemoteProductMixin, WooCommercePayloadMixin


import logging
logger = logging.getLogger(__name__)


class WoocommerceProductContentUpdateFactory(WooCommerceUpdateRemoteProductMixin,
        WooCommercePayloadMixin, RemoteProductContentUpdateFactory):
    remote_model_class = WoocommerceProductContent

    def update_remote(self):
        return self.update_remote_product()
