import requests
from django.core.files.base import ContentFile

from contacts.demo_data import BED_SUPPLIER_NAME, GLASS_SUPPLIER_NAME, METAL_SUPPLIER_NAME, WOOD_SUPPLIER_ONE_NAME
from core.demo_data import DemoDataLibrary, PrivateStructuredDataGenerator, fake
from core.managers.decorators import multi_tenant_company_required
from core.models import MultiTenantCompany, MultiTenantUser
from media.models import MediaProductThrough, Media
from products.models import ProductTranslation, Product, BundleProduct, SimpleProduct, SupplierProduct, \
    SupplierPrice, BundleVariation, DropshipProduct, ConfigurableProduct, ConfigurableVariation
from properties.models import Property, PropertySelectValue, ProductProperty
from products.product_types import CONFIGURABLE, SIMPLE, BUNDLE, DROPSHIP
from taxes.models import VatRate
from units.models import Unit
from contacts.models import Supplier
from units.demo_data import UNIT_PIECE

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


class ProductGetDataMixin:
    def get_unit(self, unit):
        return Unit.objects.get(multi_tenant_company=self.multi_tenant_company, unit=unit)

    def get_supplier(self, name):
        return Supplier.objects.get(multi_tenant_company=self.multi_tenant_company, name=name)

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
                product_property = ProductProperty.objects.get_or_create(
                    product=product,
                    property=property_instance,
                    multi_tenant_company=self.multi_tenant_company
                )[0]
                product_property.value_multi_select.add(value_instance)

    def add_image(self, url, product):
        """Downloads an image from a URL, saves it locally, and assigns it to a product."""
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_name = url.split("/")[-1]  # Extract file name from URL
            image_content = ContentFile(response.content, name=file_name)

            image = Media.objects.create(
                type=Media.IMAGE,
                image=image_content,
                owner=MultiTenantUser.objects.filter(multi_tenant_company=self.multi_tenant_company).first(),
                multi_tenant_company=self.multi_tenant_company,
            )

            MediaProductThrough.objects.create(
                product=product,
                media=image,
                sort_order=10,
                is_main_image=True,
                multi_tenant_company=self.multi_tenant_company,
            )


class PostDataTranslationMixin:
    def post_data_generate(self, instance, **kwargs):
        multi_tenant_company = instance.multi_tenant_company
        language = multi_tenant_company.language
        name = kwargs['name']

        ProductTranslation.objects.create(
            product=instance,
            language=language,
            name=name,
            multi_tenant_company=multi_tenant_company,
        )


@registry.register_private_app
class SimpleProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator):
    model = SimpleProduct

    def get_structure(self):
        return [
            # Wooden Chairs (Multiple Colors)
            {
                'instance_data': {
                    'sku': SIMPLE_CHAIR_WOOD_SKU,  # Default Blue
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Wooden Chair - Blue",
                    'color': "Blue",
                    'usage': ["Indoor", "Office"],
                    'image_url': "https://images.squarespace-cdn.com/content/v1/54bf321fe4b042c4bf4e2f67/9eab74c9-7ffd-4e7c-85b1-796362486b52/blue+seat+logo+chair+only-01.png?format=1500w",
                },
            },
            {
                'instance_data': {
                    'sku': SIMPLE_CHAIR_WOOD_RED_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Wooden Chair - Red",
                    'color': "Red",
                    'usage': ["Indoor", "Restaurant"],
                    'image_url': "https://png.pngtree.com/png-clipart/20190920/original/pngtree-red-chair-furniture-illustration-png-image_4624169.jpg",
                },
            },
            {
                'instance_data': {
                    'sku': SIMPLE_CHAIR_WOOD_GREEN_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Wooden Chair - Green",
                    'color': "Green",
                    'usage': ["Garden", "Outdoor"],
                    'image_url': "https://clipart-library.com/img1/1221331.jpg",
                },
            },
            # Metal Chair
            {
                'instance_data': {
                    'sku': SIMPLE_CHAIR_METAL_SKU,
                    'active': True,
                    'for_sale': True,
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
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Glass Table",
                    'color': None,
                    'usage': ["Office", "Restaurant"],
                    'image_url': "https://media.istockphoto.com/id/1254777704/vector/empty-glass-round-office-table-with-metal-stand-isolated-on-white-background-vector-template.jpg?s=612x612&w=0&k=20&c=zV85V-msjfYNXdmWKLdlGtwh0-isaW00qDoceH5SlQ4=",
                },
            },
            # Queen Bed
            {
                'instance_data': {
                    'sku': SIMPLE_BED_QUEEN_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Queen Size Bed",
                    'color': None,
                    'usage': ["Hotel"],
                    'image_url': "https://media.istockphoto.com/id/1326913001/vector/double-size-bed-semi-flat-color-vector-object.jpg?s=612x612&w=0&k=20&c=atbKusfJrh8GXr8SL0mNsikKGfPRC3Rn5y5JeGERO_g=",
                },
            },
        ]

    def post_data_generate(self, instance, **kwargs):
        super().post_data_generate(instance, **kwargs)

        # Assign Product Type
        product_type = self.get_product_type("Chair" if "CHAIR" in instance.sku else "Table" if "TABLE" in instance.sku else "Bed")
        ProductProperty.objects.create(
            product=instance, property=product_type.property, value_select=product_type, multi_tenant_company=self.multi_tenant_company
        )

        # Assign Required Properties
        properties = {
            "Color": self.get_property_value("Color", kwargs.get("color")),
            "Materials": self.get_property_value("Materials"),
            "Size": self.get_property_value("Size") if "BED" in instance.sku else None,
        }

        for prop_name, value in properties.items():
            if value:
                ProductProperty.objects.create(
                    product=instance, property=value.property, value_select=value, multi_tenant_company=self.multi_tenant_company
                )

        # Assign Usage (Multi-Select Property)
        usage_values = kwargs.get("usage")
        if usage_values:
            self.assign_multi_select_property(instance, "Usage", usage_values)

        # Assign Image
        if "image_url" in kwargs:
            self.add_image(kwargs["image_url"], instance)


@registry.register_private_app
class SupplierProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator):
    model = SupplierProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': SUPPLIER_WOODEN_CHAIR_SKU,
                    'active': True,
                    'supplier': self.get_supplier(WOOD_SUPPLIER_ONE_NAME),
                },
                'post_data': {
                    'name': "Supplier - Wooden Chair",
                    'base_products_skus': [SIMPLE_CHAIR_WOOD_SKU],
                    'price_info': {
                        'quantity': 10,
                        'unit_price': 50.0,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_METAL_CHAIR_SKU,
                    'active': True,
                    'supplier': self.get_supplier(METAL_SUPPLIER_NAME),
                },
                'post_data': {
                    'name': "Supplier - Metal Chair",
                    'base_products_skus': [SIMPLE_CHAIR_METAL_SKU],
                    'price_info': {
                        'quantity': 8,
                        'unit_price': 55.0,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_GLASS_TABLE_SKU,
                    'active': True,
                    'supplier': self.get_supplier(GLASS_SUPPLIER_NAME),
                },
                'post_data': {
                    'name': "Supplier - Glass Table",
                    'base_products_skus': [SIMPLE_TABLE_GLASS_SKU],
                    'price_info': {
                        'quantity': 5,
                        'unit_price': 150.0,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_QUEEN_BED_SKU,
                    'active': True,
                    'supplier': self.get_supplier(BED_SUPPLIER_NAME),
                },
                'post_data': {
                    'name': "Supplier - Queen Bed",
                    'base_products_skus': [SIMPLE_BED_QUEEN_SKU],
                    'price_info': {
                        'quantity': 3,
                        'unit_price': 400.0,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
        ]

    def post_data_generate(self, instance, **kwargs):
        super().post_data_generate(instance, **kwargs)

        for sku in kwargs['base_products_skus']:
            base_product = self.get_product(sku)
            instance.base_products.add(base_product)

@registry.register_private_app
class ConfigurableProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator):
    model = ConfigurableProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': CONFIGURABLE_CHAIR_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Customizable Wooden Chair",
                    'image_url': "https://images.squarespace-cdn.com/content/v1/54bf321fe4b042c4bf4e2f67/9eab74c9-7ffd-4e7c-85b1-796362486b52/blue+seat+logo+chair+only-01.png?format=1500w",
                },
            }
        ]

    def post_data_generate(self, instance, **kwargs):
        super().post_data_generate(instance, **kwargs)

        product_type = self.get_product_type("Chair")
        ProductProperty.objects.create(product=instance, property=product_type.property,
                                       value_select=product_type, multi_tenant_company=self.multi_tenant_company)


        # Get Wooden Chairs in different colors
        variations = [
            self.get_product(SIMPLE_CHAIR_WOOD_SKU),
            self.get_product(SIMPLE_CHAIR_WOOD_RED_SKU),
            self.get_product(SIMPLE_CHAIR_WOOD_GREEN_SKU),
        ]

        # Assign variations to Configurable Product
        for variation in variations:
            ConfigurableVariation.objects.create(parent=instance, variation=variation, multi_tenant_company=self.multi_tenant_company)

        if "image_url" in kwargs:
            self.add_image(kwargs["image_url"], instance)


@registry.register_private_app
class BundleProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator):
    model = BundleProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': BUNDLE_DINING_SET_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Dining Set (4 Chairs + 1 Table)",
                    'variations': {SIMPLE_CHAIR_WOOD_SKU: 4, SIMPLE_TABLE_GLASS_SKU: 1}
                },
            }
        ]

    def post_data_generate(self, instance, **kwargs):
        super().post_data_generate(instance, **kwargs)

        for sku, qty in kwargs['variations'].items():
            variation = self.get_product(sku)
            BundleVariation.objects.create(parent=instance, variation=variation, quantity=qty, multi_tenant_company=self.multi_tenant_company)