from products.models import Product, ProductTranslation
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation, \
    ProductPropertiesRule, ProductProperty, PropertyTranslation
from sales_prices.models import SalesPrice
from currencies.models import Currency
from sales_channels.integrations.woocommerce.factories.pulling import WoocommerceRemoteCurrencyPullFactory, \
    WoocommerceSalesChannelViewPullFactory, WoocommerceLanguagePullFactory
from sales_channels.integrations.woocommerce.factories.properties import WooCommerceGlobalAttributeCreateFactory
from sales_channels.integrations.woocommerce.models import WoocommerceCurrency, WoocommerceProduct, WoocommerceSalesChannel
from sales_channels.models import SalesChannelView, SalesChannelViewAssign

import logging
logger = logging.getLogger(__name__)


class CreateTestProductMixin:
    def setUp(self):
        super().setUp()
        pull_factory = WoocommerceRemoteCurrencyPullFactory(
            sales_channel=self.sales_channel
        )
        pull_factory.run()

        pull_factory = WoocommerceSalesChannelViewPullFactory(
            sales_channel=self.sales_channel
        )
        pull_factory.run()

        pull_factory = WoocommerceLanguagePullFactory(
            sales_channel=self.sales_channel
        )
        pull_factory.run()

        self.api = pull_factory.get_api()

        remote_currency = WoocommerceCurrency.objects.get(
            sales_channel=self.sales_channel,
        )
        remote_currency.local_instance = self.currency
        remote_currency.save()

    def tearDown(self):
        from sales_channels.integrations.woocommerce.exceptions import FailedToDeleteProductError
        for product in WoocommerceProduct.objects.filter(remote_id__isnull=False):
            try:
                self.api.delete_product(product.remote_id)
            except FailedToDeleteProductError as e:
                logger.error(f"Error deleting product {product.remote_id}: {e}")

    def create_property(self, name, is_product_type=False, type=Property.TYPES.SELECT):
        prop = Property.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=is_product_type,
            type=type,
            is_public_information=True,
            add_to_filters=True,
        )

        PropertyTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
            language=self.multi_tenant_company.language,
            name=name
        )

        return prop

    def create_property_value(self, name, prop):
        property_value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=prop,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=property_value,
            language=self.multi_tenant_company.language,
            value=name
        )
        return property_value

    def create_product_type_value(self, name):
        product_type_prop = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
        )
        value = PropertySelectValue.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            property=product_type_prop,
        )
        PropertySelectValueTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            propertyselectvalue=product_type_prop,
            language=self.multi_tenant_company.language,
            value=name
        )

        return value

    def create_test_product(self, sku, name, assign_to_sales_channel=False, rule=None, is_configurable=False):
        if is_configurable:
            ptype = Product.CONFIGURABLE
        else:
            ptype = Product.SIMPLE

        product, created = Product.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            sku=sku,
            type=ptype
        )

        if not created:
            return product

        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language=self.multi_tenant_company.language,
            name=name,
            short_description="<b>Short Description</b>",
            description="<b>Description</b>",
        )
        # Create a property for product type
        product_type_property = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
        )
        # Create a property value for "Test Type"
        test_type_value, created = PropertySelectValue.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            property=product_type_property,
        )

        if created:
            PropertySelectValueTranslation.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                propertyselectvalue=test_type_value,
                language=self.multi_tenant_company.language,
                value="Sales Channel Test"
            )

        if rule is None:
            property_rule, _ = ProductPropertiesRule.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                product_type=test_type_value,
            )
        else:
            property_rule = rule

        self.currency = Currency.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            is_default_currency=True)

        self.price, created = SalesPrice.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            currency=self.currency,
            price=90,
            rrp=100,
        )

        ProductProperty.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=product_type_property,
            value_select=test_type_value,
        )

        if assign_to_sales_channel:
            # finally we also assign the product to the sales channel
            self.sales_channel_view = SalesChannelView.objects.get(
                # multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
            )
            self.sales_channel_view_assign = SalesChannelViewAssign.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel_view=self.sales_channel_view,
                sales_channel=self.sales_channel,
                product=product,
            )

        return product
