import requests
import logging
from imports_exports.factories.imports import ImportMixin
from spapi import DefinitionsApi
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.factories.sales_channels.full_schema import ExportDefinitionFactory
from sales_channels.integrations.amazon.models import AmazonSalesChannelView
from sales_channels.integrations.amazon.models.properties import AmazonProductType, AmazonPublicDefinition, \
    AmazonProperty, AmazonPropertySelectValue, AmazonProductTypeItem
from properties.models import ProductPropertiesRuleItem, Property
from sales_channels.integrations.amazon.constants import AMAZON_INTERNAL_PROPERTIES
from sales_channels.integrations.amazon.decorators import throttle_safe
from django.utils import timezone

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

    def prepare_import_process(self):
        # during the import this needs to stay false to prevent trying to create the mirror models because
        # we create them manually
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save()

    def get_total_instances(self):
        return 100

    def _download_json(self, url, category_code=None, marketplace_id=None):
        """
        Download the JSON schema from Amazon's URL and save it to disk for inspection.
        """
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data

    @throttle_safe(max_retries=5, base_delay=1)
    def _get_schema_for_marketplace(self, view, category_code, is_default_marketplace=False):
        """
        SP-API call to get product type definition for a given marketplace view.
        Returns parsed schema JSON with optional title added.
        """
        definitions_api = DefinitionsApi(self._get_client())
        response = definitions_api.get_definitions_product_type(
            product_type=category_code,
            marketplace_ids=[view.remote_id],
            requirements="LISTING",
            seller_id=self.sales_channel.remote_id,
        )

        schema_link = response.var_schema.link.resource
        schema_data = self._download_json(schema_link)

        if is_default_marketplace:
            schema_data["title"] = response.display_name

        return schema_data

    def sync_public_definitions(self, attr_code, schema_definition, required_properties, product_type_obj, view):
        """
        Go over the parsed schema_definition and sync AmazonPublicDefinition models.
        """

        public_def, created = AmazonPublicDefinition.objects.get_or_create(
            product_type_code=product_type_obj.product_type_code,
            api_region_code=view.api_region_code,
            code=attr_code,
        )

        public_def.name = schema_definition["title"] if "title" in schema_definition else f"{attr_code} {view.api_region_code}"
        public_def.raw_schema = schema_definition
        public_def.is_required = attr_code in required_properties
        public_def.is_internal = attr_code in AMAZON_INTERNAL_PROPERTIES
        public_def.save()


        if public_def.should_refresh() and not public_def.is_internal:

            # These factories will handle smart fallback logic (for now: pass)
            export_definition_fac = ExportDefinitionFactory(public_def)
            export_definition_fac.run()

            # UsageDefinitionFactory(public_def).run()
            public_def.export_definition = export_definition_fac.results
            public_def.last_fetched = timezone.now()
            public_def.save()

        return public_def

    def create_remote_properties(self, public_definition, product_type, view, is_default):

        for property_data in public_definition.export_definition:

            remote_property, created = AmazonProperty.objects.get_or_create(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                code=property_data['code'],
                type=property_data['type'],
            )

            if created:
                allows_unmapped_values = property_data.get('allows_unmapped_values', False)
                remote_property.name = property_data['name']
                remote_property.allows_unmapped_values = allows_unmapped_values
                remote_property.save()

            if is_default:
                remote_property.name = property_data['name']
                remote_property.save()

            if remote_property.type in [Property.TYPES.SELECT, Property.TYPES.MULTISELECT]:
                for value in property_data['values']:
                    remote_select_value, _ = AmazonPropertySelectValue.objects.get_or_create(
                        multi_tenant_company=self.sales_channel.multi_tenant_company,
                        sales_channel=self.sales_channel,
                        marketplace=view,
                        amazon_property=remote_property,
                        remote_value=value['value'],
                    )

                    remote_select_value.remote_name = value['name']
                    remote_select_value.save()

                remote_rule_item, created_item = AmazonProductTypeItem.objects.get_or_create(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    amazon_rule=product_type,
                    remote_property=remote_property
                )

                new_type = (
                    ProductPropertiesRuleItem.REQUIRED
                    if public_definition.is_required
                    else ProductPropertiesRuleItem.OPTIONAL
                )

                if (
                    created or
                    (remote_rule_item.remote_type == ProductPropertiesRuleItem.OPTIONAL and new_type == ProductPropertiesRuleItem.REQUIRED)
                ):
                    remote_rule_item.remote_type = new_type
                    remote_rule_item.save()

    def get_rules_data(self):
        # raise Exception("Some error")
        sales_channel_views = AmazonSalesChannelView.objects.filter(sales_channel=self.sales_channel)
        self.update_percentage()
        product_tpes = self.get_product_types()
        self.total_import_instances_cnt = len(product_tpes)

        for product_type_code in product_tpes:
            product_type, _ = AmazonProductType.objects.get_or_create(
                product_type_code=product_type_code,
                sales_channel=self.sales_channel,
                multi_tenant_company=self.sales_channel.multi_tenant_company)

            # Step 1: Get schemas for all marketplaces
            for view in sales_channel_views:
                lang = view.remote_languages.first()
                is_default = lang and self.sales_channel.country and self.sales_channel.country in lang.remote_code

                schema_data = self._get_schema_for_marketplace(view, product_type.product_type_code,
                                                               is_default_marketplace=is_default)
                required_properties = schema_data["required"]

                if is_default:
                    # create AmazonProductType the schema_data will have a title
                    product_type.name = schema_data['title']
                    product_type.save()

                properties = schema_data.get("properties", {})
                for code, schema in properties.items():
                    # create AmazonPublicDefinition we will have the thing from the view or instead we can just use the amazon domain thing like Amazon.nl or something that comes from the schema
                    # public_definition = self.get_or_create_public_definition(...)
                    # enrich public_definition with export_definition and ussage_definition
                    # then do get or create for remote items, remote property and remote select values based on public_definition.export_definition
                    # OR
                    # the first public definition like "battery" will have export_definitions as an array with all the needed things that needs created
                    # but we still need to create the public definitions for all of that as well.
                    # if schema is_internal we will not do the export_definition and ussage_definition
                    public_definition = self.sync_public_definitions(code, schema, required_properties, product_type, view)

                    if public_definition.is_internal:
                        continue

                    self.create_remote_properties(public_definition, product_type, view, is_default)

            self.update_percentage()


    def process_completed(self):
        self.sales_channel.active = self.initial_sales_channel_status
        self.sales_channel.is_importing = False
        self.sales_channel.save()
