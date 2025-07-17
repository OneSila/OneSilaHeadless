from magento.models import Product
from products.models import ProductTranslation
from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin, MagentoTranslationMixin
from sales_channels.integrations.magento2.models import MagentoProductContent


class MagentoProductContentUpdateFactory(GetMagentoAPIMixin, RemoteProductContentUpdateFactory, MagentoTranslationMixin):
    remote_model_class = MagentoProductContent

    def customize_payload(self):
        """Prepare payload with translations for each Magento language."""

        remote_languages_map = self.get_magento_languages(
            product=self.local_instance,
            language=self.language,
        )

        for lang_code, magento_langs in remote_languages_map.items():
            channel_translation = ProductTranslation.objects.filter(
                product=self.local_instance,
                language=lang_code,
                sales_channel=self.sales_channel,
            ).first()

            default_translation = ProductTranslation.objects.filter(
                product=self.local_instance,
                language=lang_code,
                sales_channel=None,
            ).first()

            translation = channel_translation or default_translation
            if not translation:
                continue

            for magento_lang in magento_langs:
                remote_code = magento_lang.store_view_code

                content = {
                    "name": translation.name,
                    "url_key": translation.url_key,
                }

                if self.sales_channel.sync_contents:
                    content["short_description"] = translation.short_description
                    content["description"] = translation.description

                self.payload[remote_code] = content

    def update_remote(self):
        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)

        for remote_code, content in self.payload.items():
            for key, value in content.items():
                setattr(self.magento_product, key, value)

            self.magento_product.save(scope=remote_code)

    def serialize_response(self, response):
        return self.magento_product.to_dict()
