from core.demo_data import DemoDataLibrary, fake, PrivateDataGenerator, PublicDataGenerator, BaseProvider
from units.models import Unit


registry = DemoDataLibrary()


@fake.add_provider
class UnitProvider(BaseProvider):
    def unit(self) -> str:
        return 'piece'


class UnitGenerator(PrivateDataGenerator):
    model = Unit
    count = 1
    field_mapper = {
        'name': fake.unit,
        'unit': fake.unit,
    }


registry.register_private_app(UnitGenerator)
