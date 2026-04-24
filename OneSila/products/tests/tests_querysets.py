from types import SimpleNamespace

from core.tests import TestCase
from core.schema.core.mixins import GetProductQuerysetMultiTenantMixin
from products.models import SimpleProduct, ProductTranslation, Product
from sales_channels.integrations.amazon.models import AmazonSalesChannel, AmazonSalesChannelView
from sales_channels.models import RejectedSalesChannelViewAssign, SalesChannelViewAssign


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

    def test_filter_has_todo_sales_channel_view(self):
        sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        included_view = AmazonSalesChannelView.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            include_in_todo=True,
        )
        excluded_view = AmazonSalesChannelView.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            include_in_todo=False,
        )
        added = SimpleProduct.objects.create(
            sku="manager-added",
            multi_tenant_company=self.multi_tenant_company,
        )
        rejected = SimpleProduct.objects.create(
            sku="manager-rejected",
            multi_tenant_company=self.multi_tenant_company,
        )
        todo = SimpleProduct.objects.create(
            sku="manager-todo",
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelViewAssign.objects.create(
            product=added,
            sales_channel=sales_channel,
            sales_channel_view=included_view,
            multi_tenant_company=self.multi_tenant_company,
        )
        RejectedSalesChannelViewAssign.objects.create(
            product=rejected,
            sales_channel_view=included_view,
            multi_tenant_company=self.multi_tenant_company,
        )
        RejectedSalesChannelViewAssign.objects.create(
            product=added,
            sales_channel_view=excluded_view,
            multi_tenant_company=self.multi_tenant_company,
        )

        todo_ids = set(Product.objects.filter_has_todo_sales_channel_view().values_list("id", flat=True))
        completed_ids = set(Product.objects.filter_has_todo_sales_channel_view(value=False).values_list("id", flat=True))

        self.assertEqual(todo_ids, {todo.id})
        self.assertIn(added.id, completed_ids)
        self.assertIn(rejected.id, completed_ids)
        self.assertNotIn(todo.id, completed_ids)

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
