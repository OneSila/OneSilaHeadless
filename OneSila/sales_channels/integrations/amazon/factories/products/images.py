import json

from media.models import Media, MediaProductThrough
from sales_channels.factories.products.images import (
    RemoteMediaProductThroughCreateFactory,
    RemoteMediaProductThroughUpdateFactory,
    RemoteMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.amazon.factories.mixins import (
    GetAmazonAPIMixin,
    AmazonListingIssuesMixin,
)
from sales_channels.integrations.amazon.models.products import (
    AmazonImageProductAssociation,
)


class AmazonMediaProductThroughBase(GetAmazonAPIMixin, AmazonListingIssuesMixin):
    """Common logic for Amazon media-product associations."""

    remote_model_class = AmazonImageProductAssociation

    OFFER_KEYS = [
        "main_offer_image_locator",
        *[f"other_offer_image_locator_{i}" for i in range(1, 6)],
    ]
    PRODUCT_KEYS = [
        "main_product_image_locator",
        *[f"other_product_image_locator_{i}" for i in range(1, 9)],
    ]

    def __init__(self, *args, view=None, get_value_only=False, **kwargs):
        self.view = view
        self.get_value_only = get_value_only
        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_images(self):
        product = self.remote_product.local_instance
        throughs = (
            MediaProductThrough.objects.filter(
                product=product, media__type=Media.IMAGE
            )
            .order_by("sort_order")
        )
        return [t.media.image_web_url for t in throughs if t.media.image_web_url]

    def build_attributes(self):
        urls = self._get_images()
        attrs = {}
        for idx, key in enumerate(self.OFFER_KEYS):
            attrs[key] = [{"media_location": urls[idx]}] if idx < len(urls) else None
        for idx, key in enumerate(self.PRODUCT_KEYS):
            attrs[key] = [{"media_location": urls[idx]}] if idx < len(urls) else None
        return attrs

    def build_body(self):
        return {
            "productType": self.remote_product.remote_type,
            "requirements": "LISTING",
            "attributes": self.build_attributes(),
        }

    def patch_listings(self, body):
        if self.get_value_only:
            return body["attributes"]
        current_attrs = self.get_listing_attributes(
            self.remote_product.remote_sku,
            self.view.remote_id,
        )
        response = self.update_product(
            self.remote_product.remote_sku,
            self.view.remote_id,
            self.remote_product.remote_type,
            current_attrs,
            body.get("attributes", {}),
        )
        self.update_assign_issues(getattr(response, "issues", []))
        return response

    def build_payload(self):
        # override default payload building from base factories
        self.payload = {}
        return self.payload

    def serialize_response(self, response):
        return json.dumps(response.payload) if hasattr(response, "payload") else True

    def needs_update(self):
        return True


class AmazonMediaProductThroughCreateFactory(AmazonMediaProductThroughBase, RemoteMediaProductThroughCreateFactory):
    def create_remote(self):
        body = self.build_body()
        return self.patch_listings(body)

    def customize_remote_instance_data(self):
        self.remote_instance_data["remote_product"] = self.remote_product
        return self.remote_instance_data

    def set_remote_id(self, response):
        pass


class AmazonMediaProductThroughUpdateFactory(
    AmazonMediaProductThroughBase, RemoteMediaProductThroughUpdateFactory
):
    create_factory_class = AmazonMediaProductThroughCreateFactory

    def update_remote(self):
        body = self.build_body()
        return self.patch_listings(body)

    def customize_remote_instance_data(self):
        self.remote_instance_data["remote_product"] = self.remote_product
        return self.remote_instance_data


class AmazonMediaProductThroughDeleteFactory(
    AmazonMediaProductThroughBase, RemoteMediaProductThroughDeleteFactory
):
    delete_remote_instance = True

    def delete_remote(self):
        body = self.build_body()
        return self.patch_listings(body)
