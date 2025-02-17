from contacts.models import InventoryShippingAddress, InternalShippingAddress
from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PrivateStructuredDataGenerator, \
    PublicDataGenerator
from inventory.models import InventoryLocation, Inventory
from products.models import SupplierProduct
from products.demo_data import SUPPLIER_WOODEN_CHAIR_SKU, SUPPLIER_METAL_CHAIR_SKU, SUPPLIER_GLASS_TABLE_SKU, SUPPLIER_QUEEN_BED_SKU
from contacts.demo_data import INTERNAL_SHIPPING_STREET_ONE, INTERNAL_SHIPPING_STREET_TWO
registry = DemoDataLibrary()

LOCATION_WAREHOUSE_A = "Warehouse A"
LOCATION_WAREHOUSE_B = "Warehouse B"
LOCATION_B21AC = "B21AC"
LOCATION_B21AD = "B21AD"
LOCATION_B21AF = "B21AF"


@registry.register_private_app
class InventoryLocationGenerator(PrivateStructuredDataGenerator):
    model = InventoryLocation

    def get_internal_shipping_address(self, street):
        return InternalShippingAddress.objects.get(multi_tenant_company=self.multi_tenant_company,
            address1=street)

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "name": LOCATION_WAREHOUSE_A,
                    "precise": False,
                    "shippingaddress": self.get_internal_shipping_address(INTERNAL_SHIPPING_STREET_ONE),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": LOCATION_WAREHOUSE_B,
                    "precise": False,
                    "shippingaddress": self.get_internal_shipping_address(INTERNAL_SHIPPING_STREET_ONE),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": LOCATION_B21AC,
                    "precise": True,
                    "shippingaddress": self.get_internal_shipping_address(INTERNAL_SHIPPING_STREET_TWO),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": LOCATION_B21AD,
                    "precise": True,
                    "shippingaddress": self.get_internal_shipping_address(INTERNAL_SHIPPING_STREET_TWO),
                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "name": LOCATION_B21AF,
                    "precise": True,
                    "shippingaddress": self.get_internal_shipping_address(INTERNAL_SHIPPING_STREET_TWO),
                },
                'post_data': {},
            }
        ]


@registry.register_private_app
class InventoryGenerator(PrivateStructuredDataGenerator):
    model = Inventory

    def get_inventory_location(self, name):
        return InventoryLocation.objects.get(name=name, multi_tenant_company=self.multi_tenant_company)

    def get_supplier_product(self, sku):
        return SupplierProduct.objects.get(sku=sku, multi_tenant_company=self.multi_tenant_company)

    def get_structure(self):
        return [
            {
                'instance_data': {
                    "quantity": 1,
                    "inventorylocation": self.get_inventory_location(LOCATION_WAREHOUSE_A),
                    "product": self.get_supplier_product(SUPPLIER_WOODEN_CHAIR_SKU),

                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "quantity": 10,
                    "inventorylocation": self.get_inventory_location(LOCATION_B21AC),
                    "product": self.get_supplier_product(SUPPLIER_WOODEN_CHAIR_SKU),

                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "quantity": 1,
                    "inventorylocation": self.get_inventory_location(LOCATION_B21AD),
                    "product": self.get_supplier_product(SUPPLIER_METAL_CHAIR_SKU),

                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "quantity": 10,
                    "inventorylocation": self.get_inventory_location(LOCATION_B21AF),
                    "product": self.get_supplier_product(SUPPLIER_GLASS_TABLE_SKU),

                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "quantity": 2,
                    "inventorylocation": self.get_inventory_location(LOCATION_WAREHOUSE_A),
                    "product": self.get_supplier_product(SUPPLIER_QUEEN_BED_SKU),

                },
                'post_data': {},
            },
            {
                'instance_data': {
                    "quantity": 4,
                    "inventorylocation": self.get_inventory_location(LOCATION_WAREHOUSE_B),
                    "product": self.get_supplier_product(SUPPLIER_QUEEN_BED_SKU),

                },
                'post_data': {},
            },
        ]
