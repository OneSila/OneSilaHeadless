from pathlib import Path

from core.demo_data import DemoDataLibrary, PrivateStructuredDataGenerator, fake, CreatePrivateDataRelationMixin
from core.models import MultiTenantCompany, MultiTenantUser
from media.models import MediaProductThrough, Media
from products.models import (ProductTranslation, Product, BundleProduct, SimpleProduct,  BundleVariation
, ConfigurableProduct, ConfigurableVariation)
from properties.models import Property, PropertySelectValue, ProductProperty
from taxes.models import VatRate
from units.models import Unit
import os
from django.core.files import File

registry = DemoDataLibrary()

# SKUs for Simple Products
SIMPLE_CHAIR_WOOD_SKU = "CHAIR-WOOD-001"  # Default (Blue)
SIMPLE_CHAIR_WOOD_RED_SKU = "CHAIR-WOOD-002-RED"
SIMPLE_CHAIR_WOOD_GREEN_SKU = "CHAIR-WOOD-003-GREEN"
SIMPLE_CHAIR_METAL_SKU = "CHAIR-METAL-004"
SIMPLE_TABLE_GLASS_SKU = "TABLE-GLASS-005"
SIMPLE_BED_QUEEN_SKU = "BED-QUEEN-006"

# SKUs for Configurable and Bundle Products
CONFIGURABLE_CHAIR_SKU = "CHAIR-CONFIG-007"
BUNDLE_DINING_SET_SKU = "BUNDLE-DINING-SET-008"

# SKUs for Supplier Products
SUPPLIER_WOODEN_CHAIR_SKU = "SUPP-WOODEN-CHAIR"
SUPPLIER_METAL_CHAIR_SKU = "SUPP-METAL-CHAIR"
SUPPLIER_GLASS_TABLE_SKU = "SUPP-GLASS-TABLE"
SUPPLIER_QUEEN_BED_SKU = "SUPP-QUEEN-BED"


class ProductGetDataMixin(CreatePrivateDataRelationMixin):
    def get_unit(self, unit):
        return Unit.objects.get(multi_tenant_company=self.multi_tenant_company, unit=unit)

    def get_vat_rate(self):
        return VatRate.objects.filter(multi_tenant_company=self.multi_tenant_company).last()

    def get_product(self, sku):
        return Product.objects.get(multi_tenant_company=self.multi_tenant_company, sku=sku)

    def get_property_value(self, property_name, value_filter=None):
        """Returns a PropertySelectValue for a given property, optionally filtered by a specific value."""
        property_instance = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            propertytranslation__name=property_name
        )

        queryset = PropertySelectValue.objects.filter(property=property_instance)

        if value_filter:
            queryset = queryset.filter(propertyselectvaluetranslation__value=value_filter)

        return queryset.order_by("?").first() if queryset.exists() else None

    def get_product_type(self, product_type_name):
        """Returns the correct Product Type Property Value."""
        return PropertySelectValue.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            property__is_product_type=True,
            propertyselectvaluetranslation__value=product_type_name,
        )

    def assign_multi_select_property(self, product, property_name, values):
        """Assigns a multi-select property (e.g., Usage) to a product."""
        property_instance = Property.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            propertytranslation__name=property_name
        )

        for value in values:
            value_instance = PropertySelectValue.objects.filter(property=property_instance,
                                                                propertyselectvaluetranslation__value=value).first()
            if value_instance:
                product_property, created = ProductProperty.objects.get_or_create(
                    product=product,
                    property=property_instance,
                    multi_tenant_company=self.multi_tenant_company
                )

                if created:
                    self.create_demo_data_relation(product_property)

                product_property.value_multi_select.add(value_instance)

    def add_image(self, filename, product):
        image_path = os.path.join(Path(__file__).resolve().parent, 'demo_data_resources', filename)

        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                image_content = File(img_file, name=filename)

                image = Media.objects.create(
                    type=Media.IMAGE,
                    image=image_content,
                    owner=MultiTenantUser.objects.filter(multi_tenant_company=self.multi_tenant_company).first(),
                    multi_tenant_company=self.multi_tenant_company,
                )

                media_relation = MediaProductThrough.objects.create(
                    product=product,
                    media=image,
                    sort_order=10,
                    is_main_image=True,
                    multi_tenant_company=self.multi_tenant_company,
                )
                self.create_demo_data_relation(image)
                self.create_demo_data_relation(media_relation)


class PostDataTranslationMixin(CreatePrivateDataRelationMixin):
    def post_data_generate(self, instance, **kwargs):
        multi_tenant_company = instance.multi_tenant_company
        language = multi_tenant_company.language
        name = kwargs['name']

        translation = ProductTranslation.objects.create(
            product=instance,
            language=language,
            name=name,
            multi_tenant_company=multi_tenant_company,
        )

        self.create_demo_data_relation(translation)


@registry.register_private_app
class SimpleProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator, CreatePrivateDataRelationMixin):
    model = SimpleProduct

    def get_structure(self):
        return [
            # Wooden Chairs (Multiple Colors)
            {
                'instance_data': {
                    'sku': SIMPLE_CHAIR_WOOD_SKU,  # Default Blue
                    'active': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Wooden Chair - Blue",
                    'color': "Blue",
                    'usage': ["Indoor", "Office"],
                    'image_filename': "blue_chair.png",
                },
            },
            {
                'instance_data': {
                    'sku': SIMPLE_CHAIR_WOOD_RED_SKU,
                    'active': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Wooden Chair - Red",
                    'color': "Red",
                    'usage': ["Indoor", "Restaurant"],
                    'image_filename': "red_chair.jpg",
                },
            },
            {
                'instance_data': {
                    'sku': SIMPLE_CHAIR_WOOD_GREEN_SKU,
                    'active': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Wooden Chair - Green",
                    'color': "Green",
                    'usage': ["Garden", "Outdoor"],
                    'image_filename': "green_chair.jpg",
                },
            },
            # Metal Chair
            {
                'instance_data': {
                    'sku': SIMPLE_CHAIR_METAL_SKU,
                    'active': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Metal Chair",
                    'color': None,
                    'usage': ["Office"],
                },
            },
            # Glass Table
            {
                'instance_data': {
                    'sku': SIMPLE_TABLE_GLASS_SKU,
                    'active': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Glass Table",
                    'color': None,
                    'usage': ["Office", "Restaurant"],
                    'image_filename': "glass_table.jpg",
                },
            },
            # Queen Bed
            {
                'instance_data': {
                    'sku': SIMPLE_BED_QUEEN_SKU,
                    'active': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Queen Size Bed",
                    'color': None,
                    'usage': ["Hotel"],
                    'image_filename': "bed.jpg",
                },
            },
        ]

    def post_data_generate(self, instance, **kwargs):
        super().post_data_generate(instance, **kwargs)

        # Assign Product Type
        product_type = self.get_product_type("Chair" if "CHAIR" in instance.sku else "Table" if "TABLE" in instance.sku else "Bed")
        product_type_property = ProductProperty.objects.create(product=instance, property=product_type.property, value_select=product_type, multi_tenant_company=self.multi_tenant_company)

        self.create_demo_data_relation(product_type_property)

        # Assign Required Properties
        properties = {
            "Color": self.get_property_value("Color", kwargs.get("color")),
            "Materials": self.get_property_value("Materials"),
            "Size": self.get_property_value("Size") if "BED" in instance.sku else None,
        }

        for prop_name, value in properties.items():
            if value:
                product_property = ProductProperty.objects.create(product=instance, property=value.property, value_select=value, multi_tenant_company=self.multi_tenant_company)
                self.create_demo_data_relation(product_property)

        # Assign Usage (Multi-Select Property)
        usage_values = kwargs.get("usage")
        if usage_values:
            self.assign_multi_select_property(instance, "Usage", usage_values)

        # Assign Image
        if "image_filename" in kwargs:
            self.add_image(kwargs["image_filename"], instance)


@registry.register_private_app
class ConfigurableProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator, CreatePrivateDataRelationMixin):
    model = ConfigurableProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': CONFIGURABLE_CHAIR_SKU,
                    'active': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Customizable Wooden Chair",
                    'image_filename': "blue_chair.png",
                },
            }
        ]

    def post_data_generate(self, instance, **kwargs):
        super().post_data_generate(instance, **kwargs)

        product_type = self.get_product_type("Chair")
        product_type_property = ProductProperty.objects.create(product=instance, property=product_type.property,
                                       value_select=product_type, multi_tenant_company=self.multi_tenant_company)

        self.create_demo_data_relation(product_type_property)

        # Get Wooden Chairs in different colors
        variations = [
            self.get_product(SIMPLE_CHAIR_WOOD_SKU),
            self.get_product(SIMPLE_CHAIR_WOOD_RED_SKU),
            self.get_product(SIMPLE_CHAIR_WOOD_GREEN_SKU),
        ]

        # Assign variations to Configurable Product
        for variation in variations:
            config_variation = ConfigurableVariation.objects.create(parent=instance, variation=variation, multi_tenant_company=self.multi_tenant_company)
            self.create_demo_data_relation(config_variation)

        if "image_filename" in kwargs:
            self.add_image(kwargs["image_filename"], instance)


# @registry.register_private_app
# class BundleProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator, CreatePrivateDataRelationMixin):
#     model = BundleProduct
#
#     def get_structure(self):
#         return [
#             {
#                 'instance_data': {
#                     'sku': BUNDLE_DINING_SET_SKU,
#                     'active': True,
#                     'vat_rate': self.get_vat_rate(),
#                 },
#                 'post_data': {
#                     'name': "Dining Set (4 Chairs + 1 Table)",
#                     'variations': {SIMPLE_CHAIR_WOOD_SKU: 4, SIMPLE_TABLE_GLASS_SKU: 1}
#                 },
#             }
#         ]
#
#     def post_data_generate(self, instance, **kwargs):
#         super().post_data_generate(instance, **kwargs)
#
#         for sku, qty in kwargs['variations'].items():
#             variation = self.get_product(sku)
#             bundle_variation = BundleVariation.objects.create(parent=instance, variation=variation, quantity=qty, multi_tenant_company=self.multi_tenant_company)
#             self.create_demo_data_relation(bundle_variation)
