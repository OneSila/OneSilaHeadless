from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator
from products.models import Product
from contacts.models import Company, InvoiceAddress, ShippingAddress, Supplier
from currencies.models import Currency
from units.models import Unit
from .models import SupplierProduct, PurchaseOrder, PurchaseOrderItem

registry = DemoDataLibrary()

@registry.register_private_app
class SupplierProductGenerator(PrivateDataGenerator):
    model = SupplierProduct
    count = 100

    field_mapper = {
        'sku': lambda: fake.bothify(text='SKU-####??'),
        'name': lambda: fake.ecommerce_name(),
        'quantity': lambda: fake.random_int(min=1, max=100),
        'unit_price': lambda: round(fake.random_number(digits=2) + fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1), 2)
    }

    def prep_baker_kwargs(self, seed):
        super_kwargs = super().prep_baker_kwargs(seed)
        product = Product.objects.filter(type=Product.VARIATION).order_by('?').first()
        supplier = Supplier.objects.filter(is_supplier=True).order_by('?').first()
        currency = Currency.objects.filter(iso_code__in=['GBP', 'USD', 'EUR', 'THB']).order_by('?').first()
        unit = Unit.objects.order_by('?').first()

        super_kwargs.update({
            'product': product,
            'supplier': supplier,
            'currency': currency,
            'unit': unit
        })

        return super_kwargs

@registry.register_private_app
class PurchaseOrderGenerator(PrivateDataGenerator):
    model = PurchaseOrder
    count = 50

    field_mapper = {
        'order_reference': fake.order_reference,
        'status': lambda: fake.random_element(elements=(PurchaseOrder.DRAFT,
                                                        PurchaseOrder.ORDERED,
                                                        PurchaseOrder.CONFIRMED,
                                                        PurchaseOrder.PENDING_DELIVERY,
                                                        PurchaseOrder.DELIVERED))
    }

    def prep_baker_kwargs(self, seed):
        super_kwargs = super().prep_baker_kwargs(seed)
        supplier = Supplier.objects.filter(is_supplier=True).order_by('?').first()
        currency = Currency.objects.filter(iso_code__in=['GBP', 'USD', 'EUR', 'THB']).order_by('?').first()

        invoice_address = InvoiceAddress.objects.filter(company=supplier).last()
        if not invoice_address:
            invoice_address = InvoiceAddress.objects.first()

        shipping_address = ShippingAddress.objects.filter(company=supplier).last()
        if not shipping_address:
            shipping_address = ShippingAddress.objects.first()

        super_kwargs.update({
            'supplier': supplier,
            'currency': currency,
            'invoice_address': invoice_address,
            'shipping_address': shipping_address
        })

        return super_kwargs

@registry.register_private_app
class PurchaseOrderItemGenerator(PrivateDataGenerator):
    model = PurchaseOrderItem
    count = 500

    field_mapper = {
        'quantity': lambda: fake.random_int(min=1, max=50),
        'unit_price': lambda: round(fake.random_number(digits=3) + fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1), 2)
    }

    def prep_baker_kwargs(self, seed):
        super_kwargs = super().prep_baker_kwargs(seed)
        valid = False
        attempts = 0
        max_attempts = 5

        while not valid and attempts < max_attempts:
            purchase_order = PurchaseOrder.objects.order_by('?').first()
            supplier_product = SupplierProduct.objects.order_by('?').first()

            if not PurchaseOrderItem.objects.filter(purchase_order=purchase_order, item=supplier_product).exists():
                valid = True
                super_kwargs.update({
                    'purchase_order': purchase_order,
                    'item': supplier_product
                })
            attempts += 1

        return super_kwargs
