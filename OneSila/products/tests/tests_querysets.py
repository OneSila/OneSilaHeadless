from types import SimpleNamespace

from core.tests import TestCase
from core.schema.core.mixins import GetProductQuerysetMultiTenantMixin
from products.models import SimpleProduct, ProductTranslation, Product


class GetProductQuerysetMultiTenantMixinTest(TestCase):
    def test_translated_name_access_single_query(self):
        products = []
        for i in range(2):
            product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
            ProductTranslation.objects.create(
                product=product,
                language=self.multi_tenant_company.language,
                name=f"Product {i}",
                multi_tenant_company=self.multi_tenant_company,
            )
            products.append(product)

        info = SimpleNamespace(context=SimpleNamespace(request=SimpleNamespace(user=self.user)))
        qs = GetProductQuerysetMultiTenantMixin.get_queryset(Product.objects.all(), info)

        with self.assertNumQueries(1):
            names = [p.name for p in qs]

        self.assertEqual(set(names), {"Product 0", "Product 1"})

    def test_plain_all_translated_name_multiple_queries(self):
        products = []
        for i in range(2):
            product = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
            ProductTranslation.objects.create(
                product=product,
                language=self.multi_tenant_company.language,
                name=f"Product {i}",
                multi_tenant_company=self.multi_tenant_company,
            )
            products.append(product)

        qs = Product.objects.all()
        with self.assertNumQueries((len(products) * 3) + 1):
            names = [p.name for p in qs]

        # when we use use with_translated_name for ex in frontend we have 1 query
        info = SimpleNamespace(context=SimpleNamespace(request=SimpleNamespace(user=self.user)))
        qs = GetProductQuerysetMultiTenantMixin.get_queryset(Product.objects.all(), info)
        with self.assertNumQueries(1):
            names = [p.name for p in qs]

        self.assertEqual(set(names), {"Product 0", "Product 1"})
