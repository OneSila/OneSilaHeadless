from contacts.models import InventoryShippingAddress, InternalShippingAddress
from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PrivateStructuredDataGenerator, \
    PublicDataGenerator
from inventory.models import InventoryLocation, Inventory
from products.models import SupplierProduct
from products.demo_data import SUPPLIER_BLACK_TIGER_FABRIC

registry = DemoDataLibrary()


LOCATION_WAREHOUSE_A = "Warehouse A"
LOCATION_B21AC = "B21AC"
LOCATION_B21AD = "B21AD"
LOCATION_B21AF = "B21AF"


@registry.register_private_app
class InventoryLocationGenerator(PrivateStructuredDataGenerator):
    model = InventoryLocation

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "name": LOCATION_WAREHOUSE_A,
                    "precise": False,
                    "shippingaddress": InternalShippingAddress.objects.get(multi_tenant_company=self.multi_tenant_company),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": LOCATION_B21AC,
                    "precise": True,
                    "shippingaddress": InternalShippingAddress.objects.get(multi_tenant_company=self.multi_tenant_company),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": LOCATION_B21AD,
                    "precise": True,
                    "shippingaddress": InternalShippingAddress.objects.get(multi_tenant_company=self.multi_tenant_company),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": LOCATION_B21AF,
                    "precise": True,
                    "shippingaddress": InternalShippingAddress.objects.get(multi_tenant_company=self.multi_tenant_company),
                },
                'post_data': {},
            }
        ]


@registry.register_private_app
class InventoryGenerator(PrivateStructuredDataGenerator):
    model = Inventory

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "quantity": 1,
                    "inventorylocation": InventoryLocation.objects.get(name=LOCATION_WAREHOUSE_A, multi_tenant_company=self.multi_tenant_company),
                    "product": SupplierProduct.objects.get(sku=SUPPLIER_BLACK_TIGER_FABRIC, multi_tenant_company=self.multi_tenant_company),

                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "quantity": 10,
                    "inventorylocation": InventoryLocation.objects.get(name=LOCATION_B21AC, multi_tenant_company=self.multi_tenant_company),
                    "product": SupplierProduct.objects.get(sku=SUPPLIER_BLACK_TIGER_FABRIC, multi_tenant_company=self.multi_tenant_company),

                },
                'post_data': {},
            },

        ]
