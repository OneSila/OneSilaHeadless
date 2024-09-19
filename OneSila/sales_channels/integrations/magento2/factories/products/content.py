from magento.models import Product

from products.models import ProductTranslation
from sales_channels.factories.products.content import RemoteProductContentUpdateFactory
from sales_channels.integrations.magento2.factories.mixins import GetMagentoAPIMixin
from sales_channels.integrations.magento2.models import MagentoProductContent
from sales_channels.models.sales_channels import RemoteLanguage


class MagentoProductContentUpdateFactory(GetMagentoAPIMixin, RemoteProductContentUpdateFactory):
    remote_model_class = MagentoProductContent

    def preflight_check(self):
        if not self.sales_channel.sync_contents:
            return False

        return self.preflight_check()

    def update_remote(self):
        self.magento_product: Product = self.api.products.by_sku(self.remote_product.remote_sku)
        self.response_data = {}

        remote_languages = {rl.local_instance: rl.remote_code for rl in RemoteLanguage.objects.filter(
            sales_channel=self.sales_channel
        )}

        translations = ProductTranslation.objects.filter(product=self.local_instance)
        for translation in translations:
            language_code = translation.language
            remote_code = remote_languages.get(language_code, None)

            if not remote_code:
                continue

            content = {}
            content["name"] = translation.name
            content["short_description"] = translation.short_description
            content["description"] = translation.description
            content["url_key"] = translation.url_key

            self.response_data["remote_code"] = content

            for key, value in content.items():
                setattr(self.magento_product, key, value)
                self.magento_product.save(scope=remote_code)