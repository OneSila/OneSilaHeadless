from magento.models import Product

from products.models import ProductTranslation
from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoProductContent
from sales_channels.models.sales_channels import RemoteLanguage


class MagentoProductContentUpdateFactory(GetMagentoAPIMixin, RemoteProductContentUpdateFactory):
    remote_model_class = MagentoProductContent

    def customize_payload(self):
        translations = ProductTranslation.objects.filter(product=self.local_instance)

        remote_languages = {rl.local_instance: rl.sales_channel_view.code for rl in RemoteLanguage.objects.filter(
            sales_channel=self.sales_channel
        ) if rl.sales_channel_view is not None}

        for translation in translations:
            language_code = translation.language
            remote_code = remote_languages.get(language_code, None)

            if not remote_code:
                continue

            content = {}
            content["name"] = translation.name
            content["url_key"] = translation.url_key

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


