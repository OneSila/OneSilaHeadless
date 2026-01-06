from products.models import Product, ProductTranslation
from properties.models import Property, PropertySelectValue, PropertySelectValueTranslation, \
    ProductPropertiesRule, ProductProperty, PropertyTranslation
from sales_prices.models import SalesPrice
from currencies.models import Currency
from sales_channels.integrations.woocommerce.models import WoocommerceProduct, WoocommerceGlobalAttribute
from sales_channels.models import SalesChannelView, SalesChannelViewAssign

import logging
logger = logging.getLogger(__name__)


class CreateTestProductMixin:
    def assign_product_to_sales_channel(self, product):
        from products_inspector.models import Inspector

        try:
            inspector = product.inspector
        except Inspector.DoesNotExist:
            inspector = Inspector.objects.create(
                product=product,
                has_missing_information=False,
                has_missing_optional_information=False,
            )
        else:
            inspector.has_missing_information = False
            inspector.has_missing_optional_information = False
            inspector.save(update_fields=["has_missing_information", "has_missing_optional_information"])

        if getattr(product, "is_configurable", None) and product.is_configurable():
            for variation in product.get_configurable_variations(active_only=True):
                try:
                    variation_inspector = variation.inspector
                except Inspector.DoesNotExist:
                    variation_inspector = Inspector.objects.create(
                        product=variation,
                        has_missing_information=False,
                        has_missing_optional_information=False,
                    )
                else:
                    variation_inspector.has_missing_information = False
                    variation_inspector.has_missing_optional_information = False
                    variation_inspector.save(
                        update_fields=["has_missing_information", "has_missing_optional_information"]
                    )

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
        return self.sales_channel_view_assign

    def tearDown(self):
        for product in WoocommerceProduct.objects.filter(remote_id__isnull=False):
            try:
                self.api.delete_product(product.remote_id)
            except Exception as e:
                pass

        for attr in WoocommerceGlobalAttribute.objects.filter(remote_id__isnull=False):
            try:
                self.api.delete_attribute(attr.remote_id)
            except Exception:
                pass

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

        from products_inspector.models import Inspector

        try:
            inspector = product.inspector
        except Inspector.DoesNotExist:
            inspector = Inspector.objects.create(
                product=product,
                has_missing_information=False,
                has_missing_optional_information=False,
            )
        else:
            inspector.has_missing_information = False
            inspector.has_missing_optional_information = False
            inspector.save(update_fields=["has_missing_information", "has_missing_optional_information"])

        ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            language=self.multi_tenant_company.language,
            name=name,
            short_description="<p><b>Short Description</b></p>",
            description="<p><b>Description</b></p>",
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
