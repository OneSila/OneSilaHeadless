from products.models import Product, ProductTranslation
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation, \
    ProductPropertiesRule, ProductProperty
from sales_prices.models import SalesPrice
from currencies.models import Currency


class CreateTestProductMixin:
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

        return product
