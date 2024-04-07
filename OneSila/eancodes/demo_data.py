from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from eancodes.models import EanCode


registry = DemoDataLibrary()


@registry.register_private_app
class AppModelPrivateGenerator(PrivateDataGenerator):
    model = EanCode
    count = 1200
    field_mapper = {
        'ean_code': (fake.ean, {'length': 13}),
    }
