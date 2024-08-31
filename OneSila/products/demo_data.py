import random

from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from products.models import ProductTranslation, Product
from products.product_types import MANUFACTURABLE, SIMPLE, BUNDLE, DROPSHIP
from taxes.models import VatRate


registry = DemoDataLibrary()


@registry.register_private_app
class ProductDataGenerator(PrivateDataGenerator):
    model = Product
    count = 100
    field_mapper = {
        'allow_backorder': fake.boolean,
        'active': fake.boolean,
        'for_sale': True,
    }

    def prep_baker_kwargs(self, seed):
        kwargs = super().prep_baker_kwargs(seed)
        kwargs['vat_rate'] = VatRate.objects.filter_multi_tenant(self.multi_tenant_company).last()
        kwargs['type'] = random.choice([SIMPLE, BUNDLE, DROPSHIP])
        return kwargs

    def post_generate_instance(self, instance, **kwargs):
        multi_tenant_company = instance.multi_tenant_company
        language = multi_tenant_company.language

        ProductTranslation.objects.create(
            product=instance,
            language=language,
            name=fake.ecommerce_name(),
            multi_tenant_company=multi_tenant_company,
        )
