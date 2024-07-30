from contacts.models import InternalShippingAddress
from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from inventory.models import InventoryLocation, Inventory
from products.models import SupplierProduct

registry = DemoDataLibrary()


@registry.register_private_app
class InventoryLocationGenerator(PrivateDataGenerator):
    model = InventoryLocation
    count = 4
    field_mapper = {
        'name': fake.city_suffix,
        'precise': fake.boolean,
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']
        kwargs['location'] = InternalShippingAddress.objects.\
            filter_multi_tenant(multi_tenant_company).\
            last()
        return kwargs


@registry.register_private_app
class InventoryGenerator(PrivateDataGenerator):
    model = Inventory
    count = 100
    priority = 40
    field_mapper = {
        'quantity': lambda: fake.random_int(min=1, max=50),
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        multi_tenant_company = kwargs['multi_tenant_company']
        inventorylocation = InventoryLocation.objects.\
            filter_multi_tenant(multi_tenant_company=multi_tenant_company).\
            order_by('?').\
            first()
        existing_product_ids = Inventory.objects.\
            filter_multi_tenant(multi_tenant_company=multi_tenant_company).\
            filter(inventorylocation=inventorylocation).\
            values_list('product_id', flat=True)

        supplier_product = SupplierProduct.objects.\
            filter_multi_tenant(multi_tenant_company=multi_tenant_company).\
            exclude(id__in=existing_product_ids).\
            order_by('?').\
            first()

        kwargs['inventorylocation'] = inventorylocation
        kwargs['product'] = supplier_product

        return kwargs
