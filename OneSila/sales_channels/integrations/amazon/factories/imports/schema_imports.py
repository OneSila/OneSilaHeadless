import logging
from imports_exports.factories.imports import ImportMixin
from sales_channels.integrations.amazon.factories.mixins import (
    GetAmazonAPIMixin,
    EnsureMerchantSuggestedAsinMixin,
    EnsureGtinExemptionMixin,
)
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import AmazonProductTypeRuleFactory
logger = logging.getLogger(__name__)


class AmazonSchemaImportProcessor(
    ImportMixin,
    GetAmazonAPIMixin,
    EnsureMerchantSuggestedAsinMixin,
    EnsureGtinExemptionMixin,
):
    import_properties = False
    import_select_values = False
    import_rules = True
    import_products = False

    def __init__(self, import_process, sales_channel, language=None):
        super().__init__(import_process, language)

        self.sales_channel = sales_channel
        self.initial_sales_channel_status = sales_channel.active
        self.api = self.get_api()
        self.merchant_asin_property = self._ensure_merchant_suggested_asin()
        self.gtin_exemption_property = self._ensure_gtin_exemption()

    def prepare_import_process(self):
        # during the import this needs to stay false to prevent trying to create the mirror models because
        # we create them manually
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save()

    def get_total_instances(self):
        return 100

    def import_rules_process(self):

        self.update_percentage()
        product_types = self.get_product_types()
        self.total_import_instances_cnt = len(product_types)

        for product_type_code in product_types:
            product_type_fac = AmazonProductTypeRuleFactory(
                product_type_code=product_type_code,
                sales_channel=self.sales_channel,
                merchant_asin_property=self.merchant_asin_property,
                gtin_exemption_property=self.gtin_exemption_property,
                api=self.api,
                language=self.language,
            )
            product_type_fac.run()
            self.update_percentage()

    def process_completed(self):
        self.sales_channel.active = self.initial_sales_channel_status
        self.sales_channel.is_importing = False
        self.sales_channel.save()
