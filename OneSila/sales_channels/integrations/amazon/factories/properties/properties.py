import json
from spapi import ListingsApi
from sales_channels.integrations.amazon.factories.properties.mixins import AmazonProductPropertyBaseMixin
from sales_channels.integrations.amazon.models.properties import AmazonProductProperty


from sales_channels.factories.properties.properties import (
    RemoteProductPropertyCreateFactory,
    RemoteProductPropertyUpdateFactory,
    RemoteProductPropertyDeleteFactory,
)


class AmazonProductPropertyCreateFactory(AmazonProductPropertyBaseMixin, RemoteProductPropertyCreateFactory):
    remote_model_class = AmazonProductProperty

    def __init__(self, sales_channel, local_instance, remote_product, view, api=None, skip_checks=False, get_value_only=False, language=None):
        self.view = view
        super().__init__(sales_channel, local_instance, remote_product=remote_product, api=api, skip_checks=skip_checks, get_value_only=get_value_only, language=language)

    def create_remote(self):
        body = self.create_body()
        if body is None:
            return
        api = self.get_api()
        listings = ListingsApi(self._get_client())
        response = listings.patch_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=self.remote_product.remote_sku,
            marketplace_ids=[self.view.remote_id],
            body=body,
        )
        self.update_assign_issues(getattr(response, "issues", []))
        return response

    def serialize_response(self, response):
        return json.dumps(response.payload) if hasattr(response, "payload") else True

    def post_create_process(self):
        super().post_create_process()


class AmazonProductPropertyUpdateFactory(AmazonProductPropertyBaseMixin, RemoteProductPropertyUpdateFactory):
    remote_model_class = AmazonProductProperty
    create_factory_class = AmazonProductPropertyCreateFactory

    def __init__(self, sales_channel, local_instance, remote_product, view, api=None, get_value_only=False, remote_instance=None, skip_checks=False, language=None):
        self.view = view
        super().__init__(sales_channel, local_instance, remote_product=remote_product, api=api,
              get_value_only=get_value_only, remote_instance=remote_instance, skip_checks=skip_checks, language=language)

    def update_remote(self):

        body = self.create_body()
        if body is None:
            return

        listings = ListingsApi(self._get_client())
        response = listings.patch_listings_item(
            seller_id=self.sales_channel.remote_id,
            sku=self.remote_product.remote_sku,
            marketplace_ids=[self.view.remote_id],
            body=body,
        )
        self.update_assign_issues(getattr(response, "issues", []))
        return response

    def serialize_response(self, response):
        return json.dumps(response.payload) if hasattr(response, "payload") else True

    def additional_update_check(self):
        self.local_property = self.local_instance.property
        self.remote_product = self.remote_instance.remote_product
        self.remote_property = self.remote_instance.remote_property

        product_type_code, payload = self.build_payload()
        self.remote_value = json.dumps(payload)

        if self.get_value_only:
            self.remote_instance.remote_value = self.remote_value
            self.remote_instance.save()
            return False

        return self.remote_instance.needs_update(self.remote_value)


class AmazonProductPropertyDeleteFactory(AmazonProductPropertyBaseMixin, RemoteProductPropertyDeleteFactory):
    remote_model_class = AmazonProductProperty
    delete_remote_instance = True

    def __init__(self, sales_channel, local_instance, remote_product, view, api=None, remote_instance=None):
        self.view = view
        super().__init__(sales_channel, local_instance, remote_product=remote_product, api=api, remote_instance=remote_instance)

    def delete_remote(self):
        listings = ListingsApi(self._get_client())
        try:
            response = listings.patch_listings_item(
                seller_id=self.sales_channel.remote_id,
                sku=self.remote_instance.remote_product.remote_sku,
                marketplace_ids=[self.view.remote_id],
                body={
                    "productType": self.remote_instance.remote_product.remote_type,
                    "requirements": "LISTING",
                    "attributes": {self.remote_instance.remote_property.main_code: None},
                },
            )
            self.update_assign_issues(getattr(response, "issues", []))
            return response
        except Exception:
            return True

    def serialize_response(self, response):
        return True
