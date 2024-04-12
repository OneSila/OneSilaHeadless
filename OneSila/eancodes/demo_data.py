from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from django.db.models import Q
from eancodes.models import EanCode
from products.models import Product
from products.product_types import UMBRELLA, VARIATION, BUNDLE, PRODUCT_TYPE_CHOICES

registry = DemoDataLibrary()


@registry.register_private_app
class AppModelPrivateGenerator(PrivateDataGenerator):
    model = EanCode
    count = 1200
    field_mapper = {
        'ean_code': (fake.ean, {'length': 13}),
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)

        if fake.boolean():
            kwargs['product'] = Product.objects.\
                filter(Q(type=VARIATION) | Q(type=BUNDLE)).\
                filter(eancode__isnull=True).\
                first()

        return kwargs
