from magento.exceptions import InstanceGetFailed
from magento.models import MediaEntry

from sales_channels.factories.products.images import RemoteMediaProductThroughCreateFactory, RemoteMediaProductThroughUpdateFactory, \
    RemoteMediaProductThroughDeleteFactory, RemoteImageDeleteFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoImageProductAssociation

class GetMagentoImageTypesMixin:
    def get_image_types(self):
        types = []

        if self.local_instance.is_main_image:
            types = ["thumbnail", "image", "small_image"]

        return types

class MagentoMediaProductThroughCreateFactory(GetMagentoAPIMixin, RemoteMediaProductThroughCreateFactory, GetMagentoImageTypesMixin):
    remote_model_class = MagentoImageProductAssociation
    remote_id_map = 'id'
    field_mapping = {
        'sales_channels_sort_order': 'position',
        'media__image__name': 'label',
        'media__image_web_url': 'image_url'
    }
    api_package_name = 'product_media_entries'
    api_method_name = 'create'

    def preflight_process(self):
        super().preflight_process()
        self.magento_product = self.api.products.by_sku(self.remote_product.remote_sku)
        self.api.media_entries_product = self.magento_product

    def customize_remote_instance_data(self):
        self.remote_instance_data['remote_product'] = self.remote_product
        return self.remote_instance_data

    def customize_payload(self):
        self.payload['disabled'] = False
        self.payload['media_type'] = "image"
        self.payload['types'] = self.get_image_types()

        self.payload = {'data': self.payload}
        return self.payload

    def serialize_response(self, response):
        return response.to_dict()

    def post_action_payload_modify(self):
        self.payload['is_main_image'] = self.local_instance.is_main_image

class MagentoMediaProductThroughUpdateFactory(GetMagentoAPIMixin, RemoteMediaProductThroughUpdateFactory, GetMagentoImageTypesMixin):
    remote_model_class = MagentoImageProductAssociation
    field_mapping = {
        'sales_channels_sort_order': 'position',
        'media__image__name': 'label',
    }

    def additional_update_check(self):
        self.magento_product = self.api.products.by_sku(self.remote_product.remote_sku)
        self.api.media_entries_product = self.magento_product
        self.magento_instance: MediaEntry = self.api.product_media_entries.by_id(self.remote_instance.remote_id)
        self.types = self.get_image_types()

        if self.magento_instance.position != self.local_instance.sales_channels_sort_order or self.magento_instance.types != self.types:
            return True

        return False

    def update_remote(self):
        self.magento_instance.position = self.local_instance.sales_channels_sort_order
        self.magento_instance.types = self.types
        self.magento_instance.save()

    def serialize_response(self, response):
        return self.magento_instance.to_dict()

    def post_action_payload_modify(self):
        self.payload['is_main_image'] = self.local_instance.is_main_image

    def needs_update(self):
        payload = self.payload
        payload['is_main_image'] = self.local_instance.is_main_image

        return self.remote_instance.payload != payload

class MagentoMediaProductThroughDeleteFactory(GetMagentoAPIMixin, RemoteMediaProductThroughDeleteFactory):
    remote_model_class = MagentoImageProductAssociation
    delete_remote_instance = True

    def delete_remote(self):

        try:
            magento_product = self.api.products.by_sku(self.remote_product.remote_sku)
        except InstanceGetFailed:
            return True # if the product was deleted then is no need to delete the association

        self.api.media_entries_product = magento_product
        magento_instance: MediaEntry = self.api.product_media_entries.by_id(self.remote_instance.remote_id)

        return True if magento_instance is None else magento_instance.delete()

    def serialize_response(self, response):
        return response

class MagentoImageDeleteFactory(RemoteImageDeleteFactory):
    has_remote_media_instance = False
    delete_media_assign_factory = MagentoMediaProductThroughDeleteFactory