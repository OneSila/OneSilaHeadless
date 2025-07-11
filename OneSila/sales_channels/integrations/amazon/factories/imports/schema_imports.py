import logging
from imports_exports.factories.imports import ImportMixin
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import AmazonProductTypeRuleFactory
from sales_channels.integrations.amazon.models.properties import AmazonProperty
from properties.models import Property, PropertyTranslation

logger = logging.getLogger(__name__)


class AmazonSchemaImportProcessor(ImportMixin, GetAmazonAPIMixin):
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

    def prepare_import_process(self):
        # during the import this needs to stay false to prevent trying to create the mirror models because
        # we create them manually
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save()

    def get_total_instances(self):
        return 100

    def _ensure_merchant_suggested_asin(self):
        remote_property, _ = AmazonProperty.objects.get_or_create(
            allow_multiple=True,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
            sales_channel=self.sales_channel,
            code="merchant_suggested_asin",
            defaults={"type": Property.TYPES.TEXT},
        )

        if not remote_property.local_instance:
            local_property, _ = Property.objects.get_or_create(
                internal_name="merchant_suggested_asin",
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                defaults={
                    "type": Property.TYPES.TEXT,
                    "non_deletable": True,
                },
            )

            PropertyTranslation.objects.get_or_create(
                property=local_property,
                language=self.sales_channel.multi_tenant_company.language,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                defaults={"name": "Amazon Asin"},
            )

            remote_property.local_instance = local_property
            remote_property.save()

        local_property = remote_property.local_instance
        if not local_property.non_deletable:
            local_property.non_deletable = True
            local_property.save(update_fields=["non_deletable"])

        return remote_property


    def import_rules_process(self):

        self.update_percentage()
        product_types = self.get_product_types()
        self.total_import_instances_cnt = len(product_types)

        for product_type_code in product_types:
            product_type_fac = AmazonProductTypeRuleFactory(
                product_type_code=product_type_code,
                sales_channel=self.sales_channel,
                merchant_asin_property=self.merchant_asin_property,
                api=self.api,
                language=self.language,
            )
            product_type_fac.run()
            self.update_percentage()


    def process_completed(self):
        self.sales_channel.active = self.initial_sales_channel_status
        self.sales_channel.is_importing = False
        self.sales_channel.save()


