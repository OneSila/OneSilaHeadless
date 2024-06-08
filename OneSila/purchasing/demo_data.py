from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator
from contacts.models import InvoiceAddress, ShippingAddress, Supplier
from currencies.models import Currency
from units.models import Unit
from .models import PurchaseOrder, PurchaseOrderItem
from products.models import SupplierProduct, Product, ProductTranslation, SupplierPrices

registry = DemoDataLibrary()

@registry.register_private_app
class SupplierProductGenerator(PrivateDataGenerator):
    model = SupplierProduct
    count = 100

    field_mapper = {
        'sku': lambda: fake.bothify(text='SKU-####??'),
        'type': Product.SUPPLIER
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']

        product = Product.objects.filter(type=Product.SIMPLE, multi_tenant_company=multi_tenant_company).order_by('?').first()
        supplier = Supplier.objects.filter(is_supplier=True, multi_tenant_company=multi_tenant_company).order_by('?').first()

        kwargs.update({
            'base_product': product,
            'supplier': supplier
        })

        return kwargs

    def post_generate_instance(self, instance, **kwargs):
        multi_tenant_company = instance.multi_tenant_company
        language = multi_tenant_company.language
        unit = Unit.objects.filter(multi_tenant_company=multi_tenant_company).order_by('?').first()

        ProductTranslation.objects.create(
            product=instance,
            language=language,
            name=fake.ecommerce_name(),
            multi_tenant_company=multi_tenant_company,
        )

        SupplierPrices.objects.create(
            supplier_product=instance,
            unit=unit,
            quantity=fake.random_int(min=1, max=100),
            unit_price=fake.random_int(min=1, max=1000),
            multi_tenant_company=multi_tenant_company,
        )

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
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']
        supplier = Supplier.objects.filter(is_supplier=True, multi_tenant_company=multi_tenant_company).order_by('?').first()
        currency = Currency.objects.filter(iso_code__in=['GBP', 'USD', 'EUR', 'THB'], multi_tenant_company=multi_tenant_company).order_by('?').first()

        invoice_address = InvoiceAddress.objects.filter(company=supplier, multi_tenant_company=multi_tenant_company).last()
        if not invoice_address:
            invoice_address = InvoiceAddress.objects.filter(multi_tenant_company=multi_tenant_company).first()

        shipping_address = ShippingAddress.objects.filter(company=supplier, multi_tenant_company=multi_tenant_company).last()
        if not shipping_address:
            shipping_address = ShippingAddress.objects.filter(multi_tenant_company=multi_tenant_company).first()

        kwargs.update({
            'supplier': supplier,
            'currency': currency,
            'invoice_address': invoice_address,
            'shipping_address': shipping_address
        })

        return kwargs

@registry.register_private_app
class PurchaseOrderItemGenerator(PrivateDataGenerator):
    model = PurchaseOrderItem
    count = 500

    field_mapper = {
        'quantity': lambda: fake.random_int(min=1, max=50),
        'unit_price': lambda: round(fake.random_number(digits=3) + fake.pyfloat(left_digits=0, right_digits=2, min_value=0, max_value=1), 2)
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']
        purchase_order = PurchaseOrder.objects.filter(multi_tenant_company=multi_tenant_company).order_by('?').first()
        existing_product_ids = PurchaseOrderItem.objects.filter(purchase_order=purchase_order, multi_tenant_company=multi_tenant_company).values_list('item_id', flat=True)
        supplier_product = SupplierProduct.objects.filter(multi_tenant_company=multi_tenant_company).exclude(id__in=existing_product_ids).order_by('?').first()

        kwargs.update({
            'purchase_order': purchase_order,
            'item': supplier_product,
            'multi_tenant_company': multi_tenant_company,
        })

        return kwargs
