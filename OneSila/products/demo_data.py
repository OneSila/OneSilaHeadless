from core.demo_data import DemoDataLibrary, PrivateStructuredDataGenerator
from products.models import ProductTranslation, Product, BundleProduct, SimpleProduct, SupplierProduct, \
    SupplierPrices, BundleVariation, DropshipProduct
from products.product_types import MANUFACTURABLE, SIMPLE, BUNDLE, DROPSHIP
from taxes.models import VatRate
from units.models import Unit
from contacts.models import Supplier
from contacts.demo_data import FABRIC_SUPPLIER_NAME, PEN_SUPPLIER_NAME_ONE, PEN_SUPPLIER_NAME_TWO
from units.demo_data import UNIT_METER, UNIT_PIECE

registry = DemoDataLibrary()

SIMPLE_BLACK_FABRIC_PRODUCT_SKU = "AF29-222"
SIMPLE_BLACK_FABRIC_NAME = 'Black Fabric'
SUPPLIER_BLACK_TIGER_FABRIC = '1911'

DROPSHIP_PRODUCT_VISCONTI_SKU = 'DR-2029'
DROPSHIP_PRODUCT_JAMES_SKU = 'DR-20292123'

BUNDLE_PEN_AND_INK_SKU = "B-PAI-2"
SIMPLE_PEN_SKU = 'S-P-1291'
SIMPLE_INK_SKU = 'S-I-391'
SUPPLIER_PEN_SKU_ONE = 'SUPP-PA-191'
SUPPLIER_PEN_SKU_TWO = 'SUPP-PA-192'
SUPPLIER_INK_SKU = 'SUPP-I-291'
SUPPLIER_JAMES_SKU = 'ADADF-ADFA223'

SUPPLIER_VISCONTI_SKU_ONE = 'SUPP-PA-292'
SUPPLIER_VISCONTI_SKU_TWO = 'SUPP-PA-293'


class ProductGetDataMixin:
    def get_unit(self, unit):
        return Unit.objects.get(multi_tenant_company=self.multi_tenant_company, unit=unit)

    def get_supplier(self, name):
        return Supplier.objects.get(multi_tenant_company=self.multi_tenant_company, name=name)

    def get_vat_rate(self):
        return VatRate.objects.filter(multi_tenant_company=self.multi_tenant_company).last()

    def get_product(self, sku):
        return Product.objects.get(multi_tenant_company=self.multi_tenant_company, sku=sku)


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
            {
                'instance_data': {
                    'sku': SIMPLE_BLACK_FABRIC_PRODUCT_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                    'allow_backorder': False,
                },
                'post_data': {
                    'name': SIMPLE_BLACK_FABRIC_NAME,
                },
            },
            {
                'instance_data': {
                    'sku': SIMPLE_PEN_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                    'allow_backorder': False,
                },
                'post_data': {
                    'name': "Pen",
                },
            },
            {
                'instance_data': {
                    'sku': SIMPLE_INK_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                    'allow_backorder': False,
                },
                'post_data': {
                    'name': "Ink Cartridge",
                },
            },
        ]


@registry.register_private_app
class DropshopProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator):
    model = DropshipProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': DROPSHIP_PRODUCT_VISCONTI_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "Fountain Pen Visconti",
                },
            },
            {
                'instance_data': {
                    'sku': DROPSHIP_PRODUCT_JAMES_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                },
                'post_data': {
                    'name': "James Dean Cup",
                },
            },
        ]


@registry.register_private_app
class SupplierProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator):
    model = SupplierProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': SUPPLIER_BLACK_TIGER_FABRIC,
                    'active': True,
                    'supplier': self.get_supplier(FABRIC_SUPPLIER_NAME),
                },
                'post_data': {
                    'name': 'Fabric Tiger Black',
                    'base_products_skus': [SIMPLE_BLACK_FABRIC_PRODUCT_SKU],
                    'price_info': {
                        'quantity': 1,
                        'unit_price': 9.2,
                        'unit': self.get_unit(UNIT_METER),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_PEN_SKU_ONE,
                    'active': True,
                    'supplier': self.get_supplier(PEN_SUPPLIER_NAME_ONE),
                },
                'post_data': {
                    'name': 'Pen Sameson',
                    'base_products_skus': [SIMPLE_PEN_SKU],
                    'price_info': {
                        'quantity': 1,
                        'unit_price': 40.2,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_PEN_SKU_TWO,
                    'active': True,
                    'supplier': self.get_supplier(PEN_SUPPLIER_NAME_TWO),
                },
                'post_data': {
                    'name': 'Pen James',
                    'base_products_skus': [SIMPLE_PEN_SKU],
                    'price_info': {
                        'quantity': 1,
                        'unit_price': 50.0,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_INK_SKU,
                    'active': True,
                    'supplier': self.get_supplier(PEN_SUPPLIER_NAME_ONE),
                },
                'post_data': {
                    'name': 'Fabric Tiger Black',
                    'base_products_skus': [SIMPLE_INK_SKU],
                    'price_info': {
                        'quantity': 1,
                        'unit_price': 2.2,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_VISCONTI_SKU_ONE,
                    'active': True,
                    'supplier': self.get_supplier(PEN_SUPPLIER_NAME_ONE),
                },
                'post_data': {
                    'name': 'Visconti Black Fountain Pen',
                    'base_products_skus': [DROPSHIP_PRODUCT_VISCONTI_SKU],
                    'price_info': {
                        'quantity': 1,
                        'unit_price': 422,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_VISCONTI_SKU_TWO,
                    'active': True,
                    'supplier': self.get_supplier(PEN_SUPPLIER_NAME_ONE),
                },
                'post_data': {
                    'name': 'Visconti Fountain pen black',
                    'base_products_skus': [DROPSHIP_PRODUCT_VISCONTI_SKU],
                    'price_info': {
                        'quantity': 3,
                        'unit_price': 399,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
            {
                'instance_data': {
                    'sku': SUPPLIER_JAMES_SKU,
                    'active': True,
                    'supplier': self.get_supplier(PEN_SUPPLIER_NAME_ONE),
                },
                'post_data': {
                    'name': 'James Dean Cup',
                    'base_products_skus': [DROPSHIP_PRODUCT_JAMES_SKU],
                    'price_info': {
                        'quantity': 3,
                        'unit_price': 399,
                        'unit': self.get_unit(UNIT_PIECE),
                    }
                },
            },
        ]

    def post_data_generate(self, instance, **kwargs):
        super().post_data_generate(instance, **kwargs)

        multi_tenant_company = instance.multi_tenant_company
        price_info = kwargs['price_info']
        base_products = Product.objects.\
            filter(
                sku__in=kwargs['base_products_skus'],
                multi_tenant_company=self.multi_tenant_company
            )

        for b in base_products:
            instance.base_products.add(b)

        SupplierPrices.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            supplier_product=instance,
            **price_info)


@registry.register_private_app
class BundleProductDataGenerator(PostDataTranslationMixin, ProductGetDataMixin, PrivateStructuredDataGenerator):
    model = BundleProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': BUNDLE_PEN_AND_INK_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': self.get_vat_rate(),
                    'allow_backorder': False,
                },
                'post_data': {
                    'name': "Pen with 6 Ink cartridges",
                    'variations': {SIMPLE_PEN_SKU: 1, SIMPLE_INK_SKU: 6}
                },
            }
        ]

    def post_data_generate(self, instance, **kwargs):
        super().post_data_generate(instance, **kwargs)
        multi_tenant_company = instance.multi_tenant_company
        variations = kwargs['variations']

        for sku, qty in variations.items():
            variation = self.get_product(sku)
            BundleVariation.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                parent=instance,
                variation=variation,
                quantity=qty,
            )
