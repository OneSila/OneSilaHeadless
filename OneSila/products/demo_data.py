from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from products.models import SimpleProduct
from products.product_types import UMBRELLA, SIMPLE, BUNDLE, PRODUCT_TYPE_CHOICES
from taxes.models import VatRate


registry = DemoDataLibrary()


@registry.register_private_app
class SimpleProductDataGenerator(PrivateDataGenerator):
    model = SimpleProduct
    count = 10
    field_mapper = {
        'always_on_stock': fake.boolean,
        'active': fake.boolean,
        'type': SIMPLE,
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        kwargs['vat_rate'] = VatRate.objects.last()
        return kwargs
