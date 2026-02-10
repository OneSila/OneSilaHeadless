from django.test import TransactionTestCase
from django.utils import timezone
from eancodes.models import EanCode
from sales_prices.models import SalesPrice, SalesPriceList, SalesPriceListItem
from currencies.models import Currency
from products.models import SimpleProduct, ConfigurableProduct, AliasProduct, ConfigurableVariation
from taxes.models import VatRate
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from products.product_types import CONFIGURABLE
from sales_channels.models.products import RemoteProduct
from sales_channels.models import SalesChannelViewAssign
from sales_channels.integrations.amazon.models import (
    AmazonSalesChannel,
    AmazonSalesChannelView,
    AmazonBrowseNode,
    AmazonProductBrowseNode,
)
from sales_channels.integrations.ebay.models import (
    EbaySalesChannel,
    EbaySalesChannelView,
    EbayCategory,
    EbayProductCategory,
)
from sales_channels.integrations.shein.models import (
    SheinSalesChannel,
    SheinCategory,
    SheinProductCategory,
)
from products_inspector.models import Inspector, InspectorBlock


class ProductQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_filters_test_simple_product(self):
        from .queries import SIMPLE_PRODUCT_SKU_FILTER
        simple_product, _ = SimpleProduct.objects.get_or_create(sku='test_salesprice_none_prices',
            multi_tenant_company=self.multi_tenant_company)
        resp = self.strawberry_test_client(
            query=SIMPLE_PRODUCT_SKU_FILTER,
            variables={"sku": simple_product.sku},
        )
        self.assertTrue(resp.errors is None)

    def test_search_product(self):
        from .queries import PRODUCT_SEARCH
        resp = self.strawberry_test_client(
            query=PRODUCT_SEARCH,
            variables={"search": 'some product'},
        )
        self.assertTrue(resp.errors is None)

    def test_exclude_demo_data_product(self):
        from .queries import PRODUCT_EXCLUDE_DEMO_DATA

        resp = self.strawberry_test_client(
            query=PRODUCT_EXCLUDE_DEMO_DATA,
            variables={"excludeDemoData": True},
        )

        self.assertTrue(resp.errors is None)


class ProductFilterQueryMixin:
    def _query_ids(self, *, query, variables):
        resp = self.strawberry_test_client(
            query=query,
            variables=variables,
        )
        self.assertIsNone(resp.errors)
        return {
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        }


class ProductFilterGeneralQueryTestCase(ProductFilterQueryMixin, TransactionTestCaseMixin, TransactionTestCase):

    def test_filter_by_sku(self):
        from .queries import PRODUCTS_FILTER_BY_SKU

        product = SimpleProduct.objects.create(
            sku="sku-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        SimpleProduct.objects.create(
            sku="sku-2",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_SKU,
            variables={"sku": product.sku},
        )
        self.assertSetEqual(ids, {product.id})

    def test_filter_by_type(self):
        from .queries import PRODUCTS_FILTER_BY_TYPE

        configurable = ConfigurableProduct.objects.create(
            sku="cfg-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        SimpleProduct.objects.create(
            sku="simple-1",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_TYPE,
            variables={"type": CONFIGURABLE},
        )
        self.assertSetEqual(ids, {configurable.id})

    def test_filter_exclude_type(self):
        from .queries import PRODUCTS_FILTER_EXCLUDE_TYPE

        configurable = ConfigurableProduct.objects.create(
            sku="cfg-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        simple = SimpleProduct.objects.create(
            sku="simple-1",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_EXCLUDE_TYPE,
            variables={"type": CONFIGURABLE},
        )
        self.assertSetEqual(ids, {simple.id})

    def test_filter_by_active(self):
        from .queries import PRODUCTS_FILTER_BY_ACTIVE

        active = SimpleProduct.objects.create(
            sku="active-1",
            active=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        SimpleProduct.objects.create(
            sku="inactive-1",
            active=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_ACTIVE,
            variables={"active": True},
        )
        self.assertSetEqual(ids, {active.id})

    def test_filter_by_backorder(self):
        from .queries import PRODUCTS_FILTER_BY_ALLOW_BACKORDER

        backorder = SimpleProduct.objects.create(
            sku="backorder-1",
            allow_backorder=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        SimpleProduct.objects.create(
            sku="no-backorder-1",
            allow_backorder=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_ALLOW_BACKORDER,
            variables={"allowBackorder": True},
        )
        self.assertSetEqual(ids, {backorder.id})

    def test_filter_by_vat_rate(self):
        from .queries import PRODUCTS_FILTER_BY_VAT_RATE

        vat_rate = VatRate.objects.create(
            rate=21,
            multi_tenant_company=self.multi_tenant_company,
        )
        with_rate = SimpleProduct.objects.create(
            sku="vat-1",
            vat_rate=vat_rate,
            multi_tenant_company=self.multi_tenant_company,
        )
        SimpleProduct.objects.create(
            sku="vat-2",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_VAT_RATE,
            variables={"rate": vat_rate.rate},
        )
        self.assertSetEqual(ids, {with_rate.id})

    def test_filter_by_created_at(self):
        from .queries import PRODUCTS_FILTER_BY_CREATED_AT

        older = SimpleProduct.objects.create(
            sku="created-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        newer = SimpleProduct.objects.create(
            sku="created-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        older_created_at = timezone.now() - timezone.timedelta(days=2)
        newer_created_at = timezone.now() - timezone.timedelta(hours=1)
        SimpleProduct.objects.filter(pk=older.pk).update(created_at=older_created_at)
        SimpleProduct.objects.filter(pk=newer.pk).update(created_at=newer_created_at)

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_CREATED_AT,
            variables={"createdAfter": (timezone.now() - timezone.timedelta(days=1)).isoformat()},
        )
        self.assertSetEqual(ids, {newer.id})

    def test_filter_by_updated_at(self):
        from .queries import PRODUCTS_FILTER_BY_UPDATED_AT

        older = SimpleProduct.objects.create(
            sku="updated-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        newer = SimpleProduct.objects.create(
            sku="updated-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        older_updated_at = timezone.now() - timezone.timedelta(days=2)
        newer_updated_at = timezone.now() - timezone.timedelta(hours=1)
        SimpleProduct.objects.filter(pk=older.pk).update(updated_at=older_updated_at)
        SimpleProduct.objects.filter(pk=newer.pk).update(updated_at=newer_updated_at)

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_UPDATED_AT,
            variables={"updatedAfter": (timezone.now() - timezone.timedelta(days=1)).isoformat()},
        )
        self.assertSetEqual(ids, {newer.id})

    def test_filter_by_has_ean_codes_true(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_EAN_CODES

        with_code = SimpleProduct.objects.create(
            sku="ean-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_code = SimpleProduct.objects.create(
            sku="ean-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        EanCode.objects.create(
            product=with_code,
            ean_code="1234567890128",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_HAS_EAN_CODES,
            variables={"hasEanCodes": True},
        )
        self.assertSetEqual(ids, {with_code.id})

    def test_filter_by_has_ean_codes_false(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_EAN_CODES

        with_code = SimpleProduct.objects.create(
            sku="ean-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_code = SimpleProduct.objects.create(
            sku="ean-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        EanCode.objects.create(
            product=with_code,
            ean_code="1234567890128",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_HAS_EAN_CODES,
            variables={"hasEanCodes": False},
        )
        self.assertSetEqual(ids, {without_code.id})

    def test_filter_by_has_alias_products_true(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_ALIAS_PRODUCTS

        parent = SimpleProduct.objects.create(
            sku="parent-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        AliasProduct.objects.create(
            sku="alias-1",
            alias_parent_product=parent,
            multi_tenant_company=self.multi_tenant_company,
        )
        SimpleProduct.objects.create(
            sku="no-alias-1",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_HAS_ALIAS_PRODUCTS,
            variables={"hasAliasProducts": True},
        )
        self.assertSetEqual(ids, {parent.id})

    def test_filter_by_has_alias_products_false(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_ALIAS_PRODUCTS

        parent = SimpleProduct.objects.create(
            sku="parent-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        alias = AliasProduct.objects.create(
            sku="alias-1",
            alias_parent_product=parent,
            multi_tenant_company=self.multi_tenant_company,
        )
        no_alias = SimpleProduct.objects.create(
            sku="no-alias-1",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_HAS_ALIAS_PRODUCTS,
            variables={"hasAliasProducts": False},
        )
        self.assertSetEqual(ids, {alias.id, no_alias.id})

    def test_filter_by_has_multiple_configurable_parents(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_MULTIPLE_CONFIGURABLE_PARENTS

        shared_simple = SimpleProduct.objects.create(
            sku="shared-simple-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        single_parent_simple = SimpleProduct.objects.create(
            sku="single-parent-simple-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        configurable_1 = ConfigurableProduct.objects.create(
            sku="configurable-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        configurable_2 = ConfigurableProduct.objects.create(
            sku="configurable-2",
            multi_tenant_company=self.multi_tenant_company,
        )

        ConfigurableVariation.objects.create(
            parent=configurable_1,
            variation=shared_simple,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=configurable_2,
            variation=shared_simple,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=configurable_1,
            variation=single_parent_simple,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_HAS_MULTIPLE_CONFIGURABLE_PARENTS,
            variables={"hasMultipleConfigurableParents": True},
        )
        self.assertSetEqual(ids, {shared_simple.id})

    def test_filter_by_variation_of_product_id(self):
        from .queries import PRODUCTS_FILTER_BY_VARIATION_OF_PRODUCT_ID

        variation = SimpleProduct.objects.create(
            sku="variation-lookup-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        other_variation = SimpleProduct.objects.create(
            sku="variation-lookup-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        parent_1 = ConfigurableProduct.objects.create(
            sku="variation-parent-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        parent_2 = ConfigurableProduct.objects.create(
            sku="variation-parent-2",
            multi_tenant_company=self.multi_tenant_company,
        )

        ConfigurableVariation.objects.create(
            parent=parent_1,
            variation=variation,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent_2,
            variation=variation,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent_1,
            variation=other_variation,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_VARIATION_OF_PRODUCT_ID,
            variables={"productId": self.to_global_id(variation)},
        )
        self.assertSetEqual(ids, {parent_1.id, parent_2.id})

    def test_filter_by_is_multiple_parent(self):
        from .queries import PRODUCTS_FILTER_BY_IS_MULTIPLE_PARENT

        variation_a = SimpleProduct.objects.create(
            sku="multi-parent-var-a",
            multi_tenant_company=self.multi_tenant_company,
        )
        variation_b = SimpleProduct.objects.create(
            sku="multi-parent-var-b",
            multi_tenant_company=self.multi_tenant_company,
        )
        variation_c = SimpleProduct.objects.create(
            sku="multi-parent-var-c",
            multi_tenant_company=self.multi_tenant_company,
        )

        parent_1 = ConfigurableProduct.objects.create(
            sku="multi-parent-cfg-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        parent_2 = ConfigurableProduct.objects.create(
            sku="multi-parent-cfg-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        parent_3 = ConfigurableProduct.objects.create(
            sku="multi-parent-cfg-3",
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableProduct.objects.create(
            sku="multi-parent-cfg-4",
            multi_tenant_company=self.multi_tenant_company,
        )

        ConfigurableVariation.objects.create(
            parent=parent_1,
            variation=variation_a,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent_1,
            variation=variation_b,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent_2,
            variation=variation_a,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent_3,
            variation=variation_b,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent_3,
            variation=variation_c,
            multi_tenant_company=self.multi_tenant_company,
        )

        resp = self.strawberry_test_client(
            query=PRODUCTS_FILTER_BY_IS_MULTIPLE_PARENT,
            variables={"isMultipleParent": True},
        )
        self.assertIsNone(resp.errors)
        ordered_ids = [
            int(self.from_global_id(edge["node"]["id"])[1])
            for edge in resp.data["products"]["edges"]
        ]
        self.assertListEqual(
            ordered_ids,
            [parent_1.id, parent_2.id, parent_3.id],
        )

    def test_filter_by_alias_parent_product(self):
        from .queries import PRODUCTS_FILTER_BY_ALIAS_PARENT

        parent = SimpleProduct.objects.create(
            sku="parent-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        alias = AliasProduct.objects.create(
            sku="alias-1",
            alias_parent_product=parent,
            multi_tenant_company=self.multi_tenant_company,
        )
        SimpleProduct.objects.create(
            sku="other-1",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_ALIAS_PARENT,
            variables={"parentId": self.to_global_id(parent)},
        )
        self.assertSetEqual(ids, {alias.id})

    def test_filter_by_has_prices_for_currency(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_PRICES_FOR_CURRENCY

        currency = Currency.objects.create(
            iso_code="EUR",
            name="Euro",
            symbol="€",
            multi_tenant_company=self.multi_tenant_company,
        )
        with_price = SimpleProduct.objects.create(
            sku="price-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_price = SimpleProduct.objects.create(
            sku="price-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesPrice.objects.create(
            product=with_price,
            currency=currency,
            price="9.99",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_HAS_PRICES_FOR_CURRENCY,
            variables={"currencyId": self.to_global_id(currency)},
        )
        self.assertSetEqual(ids, {with_price.id})

    def test_filter_by_missing_prices_for_currency(self):
        from .queries import PRODUCTS_FILTER_BY_MISSING_PRICES_FOR_CURRENCY

        currency = Currency.objects.create(
            iso_code="EUR",
            name="Euro",
            symbol="€",
            multi_tenant_company=self.multi_tenant_company,
        )
        with_price = SimpleProduct.objects.create(
            sku="price-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_price = SimpleProduct.objects.create(
            sku="price-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesPrice.objects.create(
            product=with_price,
            currency=currency,
            price="9.99",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_MISSING_PRICES_FOR_CURRENCY,
            variables={"currencyId": self.to_global_id(currency)},
        )
        self.assertSetEqual(ids, {without_price.id})

    def test_filter_by_has_price_list(self):
        from .queries import PRODUCTS_FILTER_BY_HAS_PRICE_LIST

        currency = Currency.objects.create(
            iso_code="EUR",
            name="Euro",
            symbol="€",
            multi_tenant_company=self.multi_tenant_company,
        )
        price_list = SalesPriceList.objects.create(
            name="Retail",
            currency=currency,
            multi_tenant_company=self.multi_tenant_company,
        )
        with_item = SimpleProduct.objects.create(
            sku="plist-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_item = SimpleProduct.objects.create(
            sku="plist-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesPriceListItem.objects.create(
            salespricelist=price_list,
            product=with_item,
            price_override="5.50",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_HAS_PRICE_LIST,
            variables={"priceListId": self.to_global_id(price_list)},
        )
        self.assertSetEqual(ids, {with_item.id})

    def test_filter_by_missing_price_list(self):
        from .queries import PRODUCTS_FILTER_BY_MISSING_PRICE_LIST

        currency = Currency.objects.create(
            iso_code="EUR",
            name="Euro",
            symbol="€",
            multi_tenant_company=self.multi_tenant_company,
        )
        price_list = SalesPriceList.objects.create(
            name="Retail",
            currency=currency,
            multi_tenant_company=self.multi_tenant_company,
        )
        with_item = SimpleProduct.objects.create(
            sku="plist-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_item = SimpleProduct.objects.create(
            sku="plist-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesPriceListItem.objects.create(
            salespricelist=price_list,
            product=with_item,
            price_override="5.50",
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_MISSING_PRICE_LIST,
            variables={"priceListId": self.to_global_id(price_list)},
        )
        self.assertSetEqual(ids, {without_item.id})

    def test_filter_by_created_at_range(self):
        from .queries import PRODUCTS_FILTER_BY_CREATED_AT_RANGE

        older = SimpleProduct.objects.create(
            sku="created-range-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        newer = SimpleProduct.objects.create(
            sku="created-range-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        older_created_at = timezone.now() - timezone.timedelta(days=5)
        newer_created_at = timezone.now() - timezone.timedelta(days=1)
        SimpleProduct.objects.filter(pk=older.pk).update(created_at=older_created_at)
        SimpleProduct.objects.filter(pk=newer.pk).update(created_at=newer_created_at)

        end_date = (timezone.now() - timezone.timedelta(days=2)).date().isoformat()
        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_CREATED_AT_RANGE,
            variables={"range": f"None,{end_date}"},
        )
        self.assertSetEqual(ids, {older.id})

    def test_filter_by_updated_at_range(self):
        from .queries import PRODUCTS_FILTER_BY_UPDATED_AT_RANGE

        older = SimpleProduct.objects.create(
            sku="updated-range-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        newer = SimpleProduct.objects.create(
            sku="updated-range-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        older_updated_at = timezone.now() - timezone.timedelta(days=5)
        newer_updated_at = timezone.now() - timezone.timedelta(days=1)
        SimpleProduct.objects.filter(pk=older.pk).update(updated_at=older_updated_at)
        SimpleProduct.objects.filter(pk=newer.pk).update(updated_at=newer_updated_at)

        start_date = (timezone.now() - timezone.timedelta(days=2)).date().isoformat()
        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_UPDATED_AT_RANGE,
            variables={"range": f"{start_date},None"},
        )
        self.assertSetEqual(ids, {newer.id})



class ProductFilterIntegrationsQueryTestCase(ProductFilterQueryMixin, TransactionTestCaseMixin, TransactionTestCase):
    def test_filter_by_assigned_to_sales_channel_view_id(self):
        from .queries import PRODUCTS_ASSIGNED_TO_VIEW_QUERY

        sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        view1 = AmazonSalesChannelView.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        view2 = AmazonSalesChannelView.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        p1 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        p3 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        SalesChannelViewAssign.objects.create(
            product=p1,
            sales_channel=sales_channel,
            sales_channel_view=view1,
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelViewAssign.objects.create(
            product=p3,
            sales_channel=sales_channel,
            sales_channel_view=view2,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_ASSIGNED_TO_VIEW_QUERY,
            variables={"view": self.to_global_id(view1)},
        )
        self.assertSetEqual(ids, {p1.id})

    def test_filter_by_not_assigned_to_sales_channel_view_id(self):
        from .queries import PRODUCTS_NOT_ASSIGNED_TO_VIEW_QUERY

        sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        view1 = AmazonSalesChannelView.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        view2 = AmazonSalesChannelView.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )
        p1 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        p2 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        p3 = SimpleProduct.objects.create(multi_tenant_company=self.multi_tenant_company)
        SalesChannelViewAssign.objects.create(
            product=p1,
            sales_channel=sales_channel,
            sales_channel_view=view1,
            multi_tenant_company=self.multi_tenant_company,
        )
        SalesChannelViewAssign.objects.create(
            product=p3,
            sales_channel=sales_channel,
            sales_channel_view=view2,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_NOT_ASSIGNED_TO_VIEW_QUERY,
            variables={"view": self.to_global_id(view1)},
        )
        self.assertSetEqual(ids, {p2.id, p3.id})

    def test_filter_by_present_on_store_sales_channel_id(self):
        from .queries import PRODUCTS_FILTER_BY_PRESENT_ON_STORE_SALES_CHANNEL

        sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        parent = ConfigurableProduct.objects.create(
            sku="parent-present-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        variation = SimpleProduct.objects.create(
            sku="variation-present-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        standalone = SimpleProduct.objects.create(
            sku="standalone-present-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        missing = SimpleProduct.objects.create(
            sku="missing-present-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent,
            variation=variation,
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteProduct.objects.create(
            local_instance=variation,
            sales_channel=sales_channel,
            remote_id="rp-var-1",
            successfully_created=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteProduct.objects.create(
            local_instance=standalone,
            sales_channel=sales_channel,
            remote_id="rp-standalone-1",
            successfully_created=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteProduct.objects.create(
            local_instance=missing,
            sales_channel=sales_channel,
            remote_id="rp-failed-1",
            successfully_created=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_PRESENT_ON_STORE_SALES_CHANNEL,
            variables={"salesChannelId": self.to_global_id(sales_channel)},
        )
        self.assertSetEqual(ids, {variation.id, standalone.id})

    def test_filter_by_not_present_on_store_sales_channel_id(self):
        from .queries import PRODUCTS_FILTER_BY_NOT_PRESENT_ON_STORE_SALES_CHANNEL

        sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        parent = ConfigurableProduct.objects.create(
            sku="parent-not-present-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        variation = SimpleProduct.objects.create(
            sku="variation-not-present-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        missing = SimpleProduct.objects.create(
            sku="missing-not-present-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent,
            variation=variation,
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteProduct.objects.create(
            local_instance=variation,
            sales_channel=sales_channel,
            remote_id="rp-var-2",
            successfully_created=True,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_NOT_PRESENT_ON_STORE_SALES_CHANNEL,
            variables={"salesChannelId": self.to_global_id(sales_channel)},
        )
        self.assertSetEqual(ids, {parent.id, missing.id})

    def test_filter_by_amazon_browser_node(self):
        from .queries import PRODUCTS_FILTER_BY_AMAZON_BROWSER_NODE

        sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        view = AmazonSalesChannelView.objects.create(
            sales_channel=sales_channel,
            remote_id="ATVPDKIKX0DER",
            multi_tenant_company=self.multi_tenant_company,
        )
        browse_node = AmazonBrowseNode.objects.create(
            remote_id="100",
            marketplace_id="ATVPDKIKX0DER",
        )
        other_browse_node = AmazonBrowseNode.objects.create(
            remote_id="200",
            marketplace_id="ATVPDKIKX0DER",
        )
        with_node = SimpleProduct.objects.create(
            sku="amz-node-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_node = SimpleProduct.objects.create(
            sku="amz-node-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProductBrowseNode.objects.create(
            product=with_node,
            sales_channel=sales_channel,
            view=view,
            recommended_browse_node_id=browse_node.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProductBrowseNode.objects.create(
            product=without_node,
            sales_channel=sales_channel,
            view=view,
            recommended_browse_node_id=other_browse_node.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_AMAZON_BROWSER_NODE,
            variables={"amazonBrowseNodeId": self.to_global_id(browse_node)},
        )
        self.assertSetEqual(ids, {with_node.id})

    def test_filter_by_exclude_amazon_browser_node(self):
        from .queries import PRODUCTS_FILTER_BY_EXCLUDE_AMAZON_BROWSER_NODE

        sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        view = AmazonSalesChannelView.objects.create(
            sales_channel=sales_channel,
            remote_id="ATVPDKIKX0DER",
            multi_tenant_company=self.multi_tenant_company,
        )
        browse_node = AmazonBrowseNode.objects.create(
            remote_id="100",
            marketplace_id="ATVPDKIKX0DER",
        )
        other_browse_node = AmazonBrowseNode.objects.create(
            remote_id="200",
            marketplace_id="ATVPDKIKX0DER",
        )
        with_node = SimpleProduct.objects.create(
            sku="amz-node-not-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_node = SimpleProduct.objects.create(
            sku="amz-node-not-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProductBrowseNode.objects.create(
            product=with_node,
            sales_channel=sales_channel,
            view=view,
            recommended_browse_node_id=browse_node.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )
        AmazonProductBrowseNode.objects.create(
            product=without_node,
            sales_channel=sales_channel,
            view=view,
            recommended_browse_node_id=other_browse_node.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_EXCLUDE_AMAZON_BROWSER_NODE,
            variables={"amazonBrowseNodeId": self.to_global_id(browse_node)},
        )
        self.assertSetEqual(ids, {without_node.id})

    def test_filter_by_ebay_product_category(self):
        from .queries import PRODUCTS_FILTER_BY_EBAY_PRODUCT_CATEGORY

        sales_channel = EbaySalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        view = EbaySalesChannelView.objects.create(
            sales_channel=sales_channel,
            default_category_tree_id="TREE-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        category = EbayCategory.objects.create(
            marketplace_default_tree_id="TREE-1",
            remote_id="123",
            name="Category 123",
            full_name="Category 123",
        )
        other_category = EbayCategory.objects.create(
            marketplace_default_tree_id="TREE-1",
            remote_id="456",
            name="Category 456",
            full_name="Category 456",
        )
        with_category = SimpleProduct.objects.create(
            sku="ebay-cat-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_category = SimpleProduct.objects.create(
            sku="ebay-cat-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        EbayProductCategory.objects.create(
            product=with_category,
            sales_channel=sales_channel,
            view=view,
            remote_id=category.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )
        EbayProductCategory.objects.create(
            product=without_category,
            sales_channel=sales_channel,
            view=view,
            remote_id=other_category.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_EBAY_PRODUCT_CATEGORY,
            variables={"ebayCategoryId": self.to_global_id(category)},
        )
        self.assertSetEqual(ids, {with_category.id})

    def test_filter_by_exclude_ebay_product_category(self):
        from .queries import PRODUCTS_FILTER_BY_EXCLUDE_EBAY_PRODUCT_CATEGORY

        sales_channel = EbaySalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        view = EbaySalesChannelView.objects.create(
            sales_channel=sales_channel,
            default_category_tree_id="TREE-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        category = EbayCategory.objects.create(
            marketplace_default_tree_id="TREE-1",
            remote_id="123",
            name="Category 123",
            full_name="Category 123",
        )
        other_category = EbayCategory.objects.create(
            marketplace_default_tree_id="TREE-1",
            remote_id="456",
            name="Category 456",
            full_name="Category 456",
        )
        with_category = SimpleProduct.objects.create(
            sku="ebay-cat-not-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_category = SimpleProduct.objects.create(
            sku="ebay-cat-not-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        EbayProductCategory.objects.create(
            product=with_category,
            sales_channel=sales_channel,
            view=view,
            remote_id=category.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )
        EbayProductCategory.objects.create(
            product=without_category,
            sales_channel=sales_channel,
            view=view,
            remote_id=other_category.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_EXCLUDE_EBAY_PRODUCT_CATEGORY,
            variables={"ebayCategoryId": self.to_global_id(category)},
        )
        self.assertSetEqual(ids, {without_category.id})

    def test_filter_by_shein_product_category(self):
        from .queries import PRODUCTS_FILTER_BY_SHEIN_PRODUCT_CATEGORY

        sales_channel = SheinSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        category = SheinCategory.objects.create(
            sales_channel=sales_channel,
            remote_id="S-100",
            name="Category S-100",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        other_category = SheinCategory.objects.create(
            sales_channel=sales_channel,
            remote_id="S-200",
            name="Category S-200",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        with_category = SimpleProduct.objects.create(
            sku="shein-cat-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_category = SimpleProduct.objects.create(
            sku="shein-cat-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinProductCategory.objects.create(
            product=with_category,
            sales_channel=sales_channel,
            remote_id=category.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinProductCategory.objects.create(
            product=without_category,
            sales_channel=sales_channel,
            remote_id=other_category.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_SHEIN_PRODUCT_CATEGORY,
            variables={"sheinCategoryId": self.to_global_id(category)},
        )
        self.assertSetEqual(ids, {with_category.id})

    def test_filter_by_exclude_shein_product_category(self):
        from .queries import PRODUCTS_FILTER_BY_EXCLUDE_SHEIN_PRODUCT_CATEGORY

        sales_channel = SheinSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )
        category = SheinCategory.objects.create(
            sales_channel=sales_channel,
            remote_id="S-100",
            name="Category S-100",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        other_category = SheinCategory.objects.create(
            sales_channel=sales_channel,
            remote_id="S-200",
            name="Category S-200",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        with_category = SimpleProduct.objects.create(
            sku="shein-cat-not-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_category = SimpleProduct.objects.create(
            sku="shein-cat-not-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinProductCategory.objects.create(
            product=with_category,
            sales_channel=sales_channel,
            remote_id=category.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinProductCategory.objects.create(
            product=without_category,
            sales_channel=sales_channel,
            remote_id=other_category.remote_id,
            multi_tenant_company=self.multi_tenant_company,
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_EXCLUDE_SHEIN_PRODUCT_CATEGORY,
            variables={"sheinCategoryId": self.to_global_id(category)},
        )
        self.assertSetEqual(ids, {without_category.id})


class ProductFilterContentQualityQueryTestCase(ProductFilterQueryMixin, TransactionTestCaseMixin, TransactionTestCase):
    def test_filter_by_missing_required_information(self):
        from .queries import PRODUCTS_FILTER_BY_MISSING_REQUIRED_INFORMATION

        required_missing = SimpleProduct.objects.create(
            sku="cq-required-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        no_required_missing = SimpleProduct.objects.create(
            sku="cq-required-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        Inspector.objects.update_or_create(
            product=required_missing,
            defaults={
                "has_missing_information": True,
                "has_missing_optional_information": False,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        Inspector.objects.update_or_create(
            product=no_required_missing,
            defaults={
                "has_missing_information": False,
                "has_missing_optional_information": True,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_MISSING_REQUIRED_INFORMATION,
            variables={},
        )
        self.assertSetEqual(ids, {required_missing.id})

    def test_filter_by_missing_information(self):
        from .queries import PRODUCTS_FILTER_BY_MISSING_INFORMATION

        has_any_missing = SimpleProduct.objects.create(
            sku="cq-missing-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        no_missing = SimpleProduct.objects.create(
            sku="cq-missing-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        Inspector.objects.update_or_create(
            product=has_any_missing,
            defaults={
                "has_missing_information": False,
                "has_missing_optional_information": True,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        Inspector.objects.update_or_create(
            product=no_missing,
            defaults={
                "has_missing_information": False,
                "has_missing_optional_information": False,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_MISSING_INFORMATION,
            variables={},
        )
        self.assertSetEqual(ids, {has_any_missing.id})

    def test_filter_by_inspector_not_successfully_code_error(self):
        from .queries import PRODUCTS_FILTER_BY_INSPECTOR_NOT_SUCCESSFULLY_CODE_ERROR

        with_error = SimpleProduct.objects.create(
            sku="cq-error-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_error = SimpleProduct.objects.create(
            sku="cq-error-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        inspector_with_error, _ = Inspector.objects.update_or_create(
            product=with_error,
            defaults={
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        inspector_without_error, _ = Inspector.objects.update_or_create(
            product=without_error,
            defaults={
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        InspectorBlock.objects.update_or_create(
            inspector=inspector_with_error,
            error_code=101,
            defaults={
                "successfully_checked": False,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        InspectorBlock.objects.update_or_create(
            inspector=inspector_without_error,
            error_code=101,
            defaults={
                "successfully_checked": True,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_INSPECTOR_NOT_SUCCESSFULLY_CODE_ERROR,
            variables={"errorCode": "101"},
        )
        self.assertSetEqual(ids, {with_error.id})

    def test_filter_by_exclude_inspector_not_successfully_code_error(self):
        from .queries import PRODUCTS_FILTER_BY_EXCLUDE_INSPECTOR_NOT_SUCCESSFULLY_CODE_ERROR

        with_error = SimpleProduct.objects.create(
            sku="cq-error-not-1",
            multi_tenant_company=self.multi_tenant_company,
        )
        without_error = SimpleProduct.objects.create(
            sku="cq-error-not-2",
            multi_tenant_company=self.multi_tenant_company,
        )
        inspector_with_error, _ = Inspector.objects.update_or_create(
            product=with_error,
            defaults={
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        inspector_without_error, _ = Inspector.objects.update_or_create(
            product=without_error,
            defaults={
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        InspectorBlock.objects.update_or_create(
            inspector=inspector_with_error,
            error_code=101,
            defaults={
                "successfully_checked": False,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )
        InspectorBlock.objects.update_or_create(
            inspector=inspector_without_error,
            error_code=101,
            defaults={
                "successfully_checked": True,
                "multi_tenant_company": self.multi_tenant_company,
            },
        )

        ids = self._query_ids(
            query=PRODUCTS_FILTER_BY_EXCLUDE_INSPECTOR_NOT_SUCCESSFULLY_CODE_ERROR,
            variables={"errorCode": "101"},
        )
        self.assertSetEqual(ids, {without_error.id})
