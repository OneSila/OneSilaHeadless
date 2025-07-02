from products.models import ProductTranslation, ProductTranslationBulletPoint
from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin, AmazonListingIssuesMixin
from sales_channels.integrations.amazon.models.products import AmazonProductContent
from sales_channels.integrations.amazon.models.properties import AmazonProductType
from spapi import ListingsApi


class AmazonProductContentUpdateFactory(GetAmazonAPIMixin, AmazonListingIssuesMixin, RemoteProductContentUpdateFactory):
    """Update product content like name and description on Amazon."""

    remote_model_class = AmazonProductContent

    def __init__(self, sales_channel, local_instance, remote_product, view, api=None, skip_checks=False, remote_instance=None, language=None):
        self.view = view
        super().__init__(
            sales_channel,
            local_instance,
            remote_product,
            api=api,
            skip_checks=skip_checks,
            remote_instance=remote_instance,
            language=language,
        )

    def _get_product_type(self):
        rule = self.local_instance.get_product_rule()
        if not rule:
            raise ValueError("Product has no product rule mapped")
        return AmazonProductType.objects.get(
            sales_channel=self.sales_channel,
            local_instance=rule,
        )

    def customize_payload(self):
        lang = (
            self.language
            or (self.view.remote_languages.first().local_instance if self.view else None)
            or self.sales_channel.multi_tenant_company.language
        )

        translation = (
            ProductTranslation.objects.filter(
                product=self.local_instance,
                language=lang,
                sales_channel=self.sales_channel,
            ).first()
            or ProductTranslation.objects.filter(
                product=self.local_instance,
                language=lang,
                sales_channel=None,
            ).first()
        )

        if not translation:
            self.payload = {}
            return

        bullet_points = list(
            ProductTranslationBulletPoint.objects.filter(
                product_translation=translation
            ).order_by("sort_order").values_list("text", flat=True)
        )

        self.payload = {
            "item_name": translation.name,
            "product_description": translation.description,
        }
        if bullet_points:
            self.payload["bullet_point"] = bullet_points

    def update_remote(self):
        if not self.payload:
            return {}

        product_type = self._get_product_type()
        body = {
            "productType": product_type.product_type_code,
            "requirements": "LISTING",
            "attributes": self.payload,
        }

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
        return response.payload if hasattr(response, "payload") else True
