from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from django.db.models import Q

from core.models import DemoDataRelation
from eancodes.models import EanCode
from products.models import Product
from products.product_types import SIMPLE, ALIAS, BUNDLE

registry = DemoDataLibrary()


@registry.register_private_app
def generate_demo_eancodes(multi_tenant_company):
    from eancodes.flows import GenerateEancodesFlow
    f = GenerateEancodesFlow(multi_tenant_company=multi_tenant_company, prefix='99999999991')
    f.flow()
    # FIXME this should be filtered on the actual product-type.
    # not "any" relation.  Much is registered in the demo-data.
    demo_data_relations = DemoDataRelation.objects.\
        filter(multi_tenant_company=multi_tenant_company).\
        values_list('object_id', flat=True)

    for instance in f.ean_codes:
        product = Product.objects.filter(
            type__in=[SIMPLE, ALIAS, BUNDLE],
            multi_tenant_company=multi_tenant_company,
            eancode__isnull=True,
            id__in=demo_data_relations
        ).first()

        # we don't want to have ean codes that we can still assign to make the onboarding work
        if product:
            instance.product = product
            instance.already_used = True
            instance.save()
            registry.create_demo_data_relation(instance)
        else:
            instance.delete()


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
            # kwargs['product'] = Product.objects.\
            #     filter(multi_tenant_company=multi_tenant_company).\
            #     filter(Q(type=SIMPLE) | Q(type=BUNDLE)).\
            #     filter(eancode__isnull=True).\
            #     first()

#         return kwargs
