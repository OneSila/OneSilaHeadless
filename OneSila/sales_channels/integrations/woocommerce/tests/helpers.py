from products.models import Product, ProductTranslation
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation, \
    ProductPropertiesRule, ProductProperty
from sales_prices.models import SalesPrice
from currencies.models import Currency
from sales_channels.integrations.woocommerce.factories.pulling import WoocommerceRemoteCurrencyPullFactory
from sales_channels.integrations.woocommerce.models import WoocommerceCurrency, WoocommerceProduct, WoocommerceSalesChannel
from sales_channels.models import SalesChannelView, SalesChannelViewAssign


class CreateTestProductMixin:
    def setUp(self):
        super().setUp()
        pull_factory = WoocommerceRemoteCurrencyPullFactory(
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
        for product in WoocommerceProduct.objects.filter(remote_id__isnull=False):
            self.api.delete_product(product.remote_id)

    def create_test_product(self, sku, name):
        product, created = Product.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            sku=sku,
            type=Product.SIMPLE
        )

        if not created:
            return product

        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language=self.multi_tenant_company.language,
            name=name
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

        property_rule, _ = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=self.multi_tenant_company,
            product_type=test_type_value,
        )

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

        # finally we also assign the product to the sales channel
        self.sales_channel_view = SalesChannelView.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.sales_channel_view_assign = SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel_view=self.sales_channel_view,
            product=product,
        )

        return product
