import json

from media.models import MediaProductThrough
from sales_channels.factories.products.images import (
    RemoteMediaProductThroughCreateFactory,
    RemoteMediaProductThroughUpdateFactory,
    RemoteMediaProductThroughDeleteFactory,
)
from sales_channels.integrations.amazon.factories.mixins import (
    GetAmazonAPIMixin,
)
from sales_channels.integrations.amazon.models.products import (
    AmazonImageProductAssociation,
)


class AmazonMediaProductThroughBase(GetAmazonAPIMixin):
    """Common logic for Amazon media-product associations."""

    remote_model_class = AmazonImageProductAssociation

    # OFFER_KEYS = [
    #     "main_offer_image_locator",
    #     *[f"other_offer_image_locator_{i}" for i in range(1, 6)],
    # ]
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
    def _get_media_url(self, *, through: MediaProductThrough) -> str | None:
        assoc = AmazonImageProductAssociation.objects.filter(
            remote_product=self.remote_product,
            local_instance=through,
        ).first()

        if assoc and assoc.imported_url:
            return assoc.imported_url
        if through.media and through.media.image_web_url:
            return through.media.image_web_url
        return None

    def _get_images(self):
        product = self.remote_product.local_instance
        throughs = MediaProductThrough.objects.get_product_images(
            product=product,
            sales_channel=self.sales_channel,
        )

        urls = []
        for t in throughs:
            url = self._get_media_url(through=t)
            if url:
                urls.append(url)

        return urls

    def build_attributes(self):
        urls = self._get_images()
        attrs = {}
        marketplace_id = self.view.remote_id if self.view else None
        swatch_through = MediaProductThrough.objects.get_product_color_image(
            product=self.remote_product.local_instance,
            sales_channel=self.sales_channel,
        )
        if swatch_through:
            swatch_url = self._get_media_url(through=swatch_through)
            if swatch_url:
                attrs["swatch_product_image_locator"] = [
                    {"marketplace_id": marketplace_id, "media_location": swatch_url}
                ]
        # for idx, key in enumerate(self.OFFER_KEYS):
        #     attrs[key] = (
        #         [{"marketplace_id": marketplace_id, "media_location": urls[idx]}]
        #         if idx < len(urls)
        #         else None
        #     )
        for idx, key in enumerate(self.PRODUCT_KEYS):
            attrs[key] = (
                [{"marketplace_id": marketplace_id, "media_location": urls[idx]}]
                if idx < len(urls)
                else None
            )
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

        response = self.update_product(
            self.remote_product.remote_sku,
            self.view.remote_id,
            self.remote_product.get_remote_rule(),
            body.get("attributes", {})
        )

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
