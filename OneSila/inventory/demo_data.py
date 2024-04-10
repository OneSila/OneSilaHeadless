from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from inventory.models import InventoryLocation


registry = DemoDataLibrary()


@registry.register_private_app
class InventoryLocationGenerator(PrivateDataGenerator):
    model = InventoryLocation
    count = 4
    field_mapper = {
        'name': fake.city_suffix,
    }