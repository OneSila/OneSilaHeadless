from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from django.db.models import Q
from eancodes.models import EanCode
from products.models import Product
from products.product_types import UMBRELLA, SIMPLE, BUNDLE, PRODUCT_TYPE_CHOICES

registry = DemoDataLibrary()


# @registry.register_private_app
# class EanCodeGenerator(PrivateDataGenerator):
#     model = EanCode
#     count = 100
#     field_mapper = {
#         'ean_code': (fake.ean, {'length': 13}),
#     }

#     def prep_baker_kwargs(self, seed):
#         kwargs = super().prep_baker_kwargs(seed)
#         multi_tenant_company = kwargs['multi_tenant_company']

#         if fake.boolean():
#             kwargs['product'] = Product.objects.\
#                 filter(multi_tenant_company=multi_tenant_company).\
#                 filter(Q(type=SIMPLE) | Q(type=BUNDLE)).\
#                 filter(eancode__isnull=True).\
#                 first()

#         return kwargs
