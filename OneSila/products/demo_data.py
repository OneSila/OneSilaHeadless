from core.demo_data import DemoDataLibrary, PrivateStructuredDataGenerator
from products.models import ProductTranslation, Product, BundleProduct, SimpleProduct, SupplierProduct, \
    SupplierPrices
from products.product_types import MANUFACTURABLE, SIMPLE, BUNDLE, DROPSHIP
from taxes.models import VatRate
from units.models import Unit
from contacts.models import Supplier
from contacts.demo_data import FABRIC_SUPPLIER_NAME
from units.demo_data import UNIT_METER

registry = DemoDataLibrary()

SIMPLE_BLACK_FABRIC_PRODUCT_SKU = "AF29-222"
SIMPLE_BLACK_FABRIC_NAME = 'Black Fabric'
SUPPLIER_BLACK_TIGER_FABRIC = '1911'


@registry.register_private_app
class SimpleProductDataGenerator(PrivateStructuredDataGenerator):
    model = SimpleProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': SIMPLE_BLACK_FABRIC_PRODUCT_SKU,
                    'active': True,
                    'for_sale': True,
                    'vat_rate': VatRate.objects.filter(multi_tenant_company=self.multi_tenant_company).last(),
                    'allow_backorder': False,
                },
                'post_data': {
                    'name': SIMPLE_BLACK_FABRIC_NAME,
                },
            }
        ]

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
class SupplierProductDataGenerator(PrivateStructuredDataGenerator):
    model = SupplierProduct

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'sku': SUPPLIER_BLACK_TIGER_FABRIC,
                    'active': True,
                    'supplier': Supplier.objects.get(multi_tenant_company=self.multi_tenant_company, name=FABRIC_SUPPLIER_NAME),
                },
                'post_data': {
                    'name': 'Fabric Tiger Black',
                    'base_products_skus': [SIMPLE_BLACK_FABRIC_PRODUCT_SKU],
                    'price_info': {
                        'quantity': 1,
                        'unit_price': 9.2,
                        'unit': Unit.objects.get(multi_tenant_company=self.multi_tenant_company, unit=UNIT_METER),
                    }
                },
            }
        ]

    def post_data_generate(self, instance, **kwargs):
        multi_tenant_company = instance.multi_tenant_company
        language = multi_tenant_company.language
        name = kwargs['name']
        price_info = kwargs['price_info']
        base_products = Product.objects.\
            filter(
                sku__in=kwargs['base_products_skus'],
                multi_tenant_company=self.multi_tenant_company
            )

        ProductTranslation.objects.create(
            product=instance,
            language=language,
            name=name,
            multi_tenant_company=multi_tenant_company,
        )

        for b in base_products:
            instance.base_products.add(b)

        SupplierPrices.objects.get_or_create(multi_tenant_company=self.multi_tenant_company,
            supplier_product=instance,
            **price_info)
