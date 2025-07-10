from products.models import ProductTranslation, ProductTranslationBulletPoint
from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models.products import AmazonProductContent
from sales_channels.integrations.amazon.models.properties import AmazonProductType


class AmazonProductContentUpdateFactory(GetAmazonAPIMixin, RemoteProductContentUpdateFactory):
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

    def preflight_check(self):
        if not self.sales_channel.listing_owner:
            return False

        return super().preflight_check()

    def _get_product_type(self):
        rule = self.local_instance.get_product_rule()
        if not rule:
            raise ValueError("Product has no product rule mapped")
        return AmazonProductType.objects.get(
            sales_channel=self.sales_channel,
            local_instance=rule,
        )

    def build_content_attributes(self):
        view_lang = (
            self.view.remote_languages.first().local_instance
            if self.view and self.view.remote_languages.exists()
            else self.sales_channel.multi_tenant_company.language
        )

        lang = self.language or view_lang

        channel_translation = ProductTranslation.objects.filter(
            product=self.local_instance,
            language=lang,
            sales_channel=self.sales_channel,
        ).first()

        default_translation = ProductTranslation.objects.filter(
            product=self.local_instance,
            language=lang,
            sales_channel=None,
        ).first()

        item_name = None
        product_description = None

        if channel_translation:
            item_name = channel_translation.name or None
            product_description = channel_translation.description or None

        if not item_name and default_translation:
            item_name = default_translation.name

        if not product_description and default_translation:
            product_description = default_translation.description

        bullet_points = []
        if channel_translation:
            bullet_points = list(
                ProductTranslationBulletPoint.objects.filter(
                    product_translation=channel_translation
                )
                .order_by("sort_order")
                .values_list("text", flat=True)
            )

        attrs = {
            "item_name": [{"value": item_name}],
            "product_description": [{"value": product_description}],
        }

        if bullet_points:
            attrs["bullet_point"] = [{"value": bp} for bp in bullet_points]

        return {k: v for k, v in attrs.items() if v not in (None, "")}

    def customize_payload(self):
        self.payload = self.build_content_attributes()

    def update_remote(self):
        if not self.payload:
            return {}

        product_type = self._get_product_type()
        body = {
            "productType": product_type.product_type_code,
            "requirements": "LISTING",
            "attributes": self.payload,
        }

        response = self.update_product(
            self.remote_product.remote_sku,
            self.view.remote_id,
            product_type,
            body.get("attributes", {}),
        )

        return response

    def serialize_response(self, response):
        return response.payload if hasattr(response, "payload") else True
