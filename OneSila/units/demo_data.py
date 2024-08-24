from core.demo_data import DemoDataLibrary, fake, PrivateDataGenerator, PublicDataGenerator, BaseProvider
from units.models import Unit


UNIT_METER = 'm'
UNIT_PIECE = 'p'

registry = DemoDataLibrary()


@registry.register_private_app
def populate_units(multi_tenant_company):
    instance, _ = Unit.objects.get_or_create(multi_tenant_company=multi_tenant_company, unit=UNIT_METER, name='Meter')
    registry.create_demo_data_relation(instance)

    instance, _ = Unit.objects.get_or_create(multi_tenant_company=multi_tenant_company, unit=UNIT_PIECE, name='Piece')
    registry.create_demo_data_relation(instance)
