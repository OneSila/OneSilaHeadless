from core.models import MultiTenantUser
from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, \
    PrivateStructuredDataGenerator
from contacts.models import InvoiceAddress, ShippingAddress, Supplier, Company, InternalCompany
from currencies.models import Currency
from units.models import Unit
from .models import PurchaseOrder, PurchaseOrderItem
from products.models import SupplierProduct, Product, ProductTranslation, SupplierPrice
from contacts.demo_data import FABRIC_SUPPLIER_NAME, INTERNAL_SHIPPING_STREET_ONE
from products.demo_data import SUPPLIER_BLACK_TIGER_FABRIC

registry = DemoDataLibrary()


@registry.register_private_app
class PurchaseOrderGenerator(PrivateStructuredDataGenerator):
    model = PurchaseOrder

    def get_user(self):
        return MultiTenantUser.objects.filter(multi_tenant_company=self.multi_tenant_company).last()

    def get_internal_company(self):
        return InternalCompany.objects.get(multi_tenant_company=self.multi_tenant_company)

    def get_invoice_address(self):
        return InvoiceAddress.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            company=self.get_internal_company())

    def get_shipping_address(self):
        return ShippingAddress.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            company=self.get_internal_company(),
            address1=INTERNAL_SHIPPING_STREET_ONE)

    def get_supplier(self):
        return Supplier.objects.get(name=FABRIC_SUPPLIER_NAME, multi_tenant_company=self.multi_tenant_company)

    def get_currency(self):
        return self.get_supplier().get_currency()

    def get_supplier_product(self, sku):
        return SupplierProduct.objects.get(sku=sku, multi_tenant_company=self.multi_tenant_company)

    def get_structure(self):
        return [
            {
                'instance_data': {
                    'supplier': self.get_supplier(),
                    'currency': self.get_currency(),
                    'order_reference': "SUP1038",
                    'status': PurchaseOrder.ORDERED,
                    'internal_contact': self.get_user(),
                    'invoice_address': self.get_invoice_address(),
                    'shipping_address': self.get_shipping_address(),
                    'internal_contact': self.get_user(),
                },
                'post_data': {
                    'purchaseorderitems': [
                        {
                            'product': self.get_supplier_product(SUPPLIER_BLACK_TIGER_FABRIC),
                            'quantity': 12,
                            'unit_price': SupplierPrice.objects.get(supplier_product=self.get_supplier_product(SUPPLIER_BLACK_TIGER_FABRIC), quantity=1).unit_price,
                        }
                    ]
                },
            },
        ]

    def post_data_generate(self, instance, **kwargs):
        items = kwargs['purchaseorderitems']
        for item in items:
            instance.purchaseorderitem_set.create(
                multi_tenant_company=self.multi_tenant_company,
                **item)
