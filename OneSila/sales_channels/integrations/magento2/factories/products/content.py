from magento.models import Product
from products.models import ProductTranslation
from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin, MagentoTranslationMixin
from sales_channels.integrations.magento2.models import MagentoProductContent


class MagentoProductContentUpdateFactory(GetMagentoAPIMixin, RemoteProductContentUpdateFactory, MagentoTranslationMixin):
    remote_model_class = MagentoProductContent

    def customize_payload(self):
        translations = ProductTranslation.objects.filter(product=self.local_instance)

        # Use the mixin to get a mapping of local language -> list of MagentoRemoteLanguage objects
        remote_languages_map = self.get_magento_languages(
            product=self.local_instance,
            language=self.language
        )

        for translation in translations:
            language_code = translation.language
            magento_languages = remote_languages_map.get(language_code, [])

            for magento_lang in magento_languages:
                remote_code = magento_lang.store_view_code

                content = {
                    "name": translation.name,
                    "url_key": translation.url_key
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


