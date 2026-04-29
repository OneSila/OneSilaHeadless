from decimal import Decimal
from unittest.mock import patch

from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from model_bakery import baker

from currencies.models import Currency
from media.models import Media, MediaProductThrough
from products.models import ConfigurableProduct, ConfigurableVariation, Product, ProductTranslation, SimpleProduct
from properties.models import (
    Property,
    PropertyTranslation,
    PropertySelectValue,
    PropertySelectValueTranslation,
    ProductProperty,
)
from sales_prices.models import SalesPrice
from sales_channels.integrations.amazon.models import AmazonSalesChannel
from sales_channels.integrations.amazon.models import AmazonProduct, AmazonProductType, AmazonSalesChannelView
from sales_channels.integrations.ebay.models import EbayProductType, EbaySalesChannel, EbaySalesChannelView
from sales_channels.integrations.mirakl.models import MiraklSalesChannel
from sales_channels.integrations.mirakl.models import MiraklProductType
from sales_channels.integrations.shein.models import SheinProductType, SheinSalesChannel
from sales_channels.models import RejectedSalesChannelViewAssign, SalesChannelViewAssign
from sales_channels.tests.helpers import DisableMiraklConnectionMixin


RESYNC_SALES_CHANNEL_VIEW_ASSIGNS_MUTATION = """
    mutation($assigns: [SalesChannelViewAssignPartialInput!]!) {
      resyncSalesChannelViewAssigns(assigns: $assigns) {
        id
      }
    }
"""


CHECK_TEMPLATE_MUTATION = """
    mutation(
        $salesChannel: SalesChannelPartialInput!
        $template: String!
        $language: String!
        $product: ProductPartialInput!
    ) {
      checkSalesChannelContentTemplate(
        salesChannel: $salesChannel
        template: $template
        language: $language
        product: $product
      ) {
        isValid
        renderedContent
        availableVariables
        errors {
          message
          severity
          validationIssue
        }
      }
    }
"""


MAP_SALES_CHANNEL_PERFECT_MATCH_SELECT_VALUES_MUTATION = """
    mutation($salesChannel: SalesChannelPartialInput!) {
      mapSalesChannelPerfectMatchSelectValues(salesChannel: $salesChannel)
    }
"""


MAP_SALES_CHANNEL_PERFECT_MATCH_PROPERTIES_MUTATION = """
    mutation($salesChannel: SalesChannelPartialInput!) {
      mapSalesChannelPerfectMatchProperties(salesChannel: $salesChannel)
    }
"""

CREATE_SALES_CHANNEL_PRODUCT_TYPES_FROM_LOCAL_RULES_MUTATION = """
    mutation($salesChannel: SalesChannelPartialInput!) {
      createSalesChannelProductTypesFromLocalRules(salesChannel: $salesChannel)
    }
"""


CHANGE_PRODUCT_VIEW_STATUS_MUTATION = """
    mutation($status: ProductViewStatus!, $assignObject: SalesChannelViewAssignObjectInput!) {
      changeProductViewStatus(status: $status, assignObject: $assignObject) {
        status
        productsCount
        viewsCount
        createdCount
        deletedCount
      }
    }
"""


CHANGE_PRODUCT_VIEWS_STATUS_MUTATION = """
    mutation($changes: [ProductViewStatusChangeInput!]!) {
      changeProductViewsStatus(changes: $changes) {
        changesCount
        createdCount
        deletedCount
      }
    }
"""


class CheckSalesChannelContentTemplateMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()

        self.sales_channel = AmazonSalesChannel.objects.create(
            hostname="https://example.com",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
        )

        ProductTranslation.objects.create(
            product=self.product,
            language=self.multi_tenant_company.language,
            name="Sample Product",
            short_description="Short copy",
            description="Long description",
            multi_tenant_company=self.multi_tenant_company,
        )

        self.currency = Currency.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            is_default_currency=True,
        ).first()

        if self.currency is None:
            self.currency = Currency.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                iso_code="EUR",
                name="Euro",
                symbol="€",
                is_default_currency=True,
            )

        SalesPrice.objects.create(
            product=self.product,
            currency=self.currency,
            rrp=Decimal("15.00"),
            price=Decimal("12.50"),
            multi_tenant_company=self.multi_tenant_company,
        )

        self.brand_property = Property.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            internal_name="brand",
        ).first()

        if self.brand_property is None:
            self.brand_property = Property.objects.create(
                multi_tenant_company=self.multi_tenant_company,
                type=Property.TYPES.SELECT,
                is_public_information=True,
                internal_name="brand",
            )

        PropertyTranslation.objects.get_or_create(
            property=self.brand_property,
            language=self.multi_tenant_company.language,
            multi_tenant_company=self.multi_tenant_company,
            defaults={
                "name": "Brand",
                "multi_tenant_company": self.multi_tenant_company,
            },
        )

        self.brand_value = PropertySelectValue.objects.create(
            property=self.brand_property,
            multi_tenant_company=self.multi_tenant_company,
        )

        PropertySelectValueTranslation.objects.create(
            propertyselectvalue=self.brand_value,
            language=self.multi_tenant_company.language,
            value="OneSila",
            multi_tenant_company=self.multi_tenant_company,
        )

        ProductProperty.objects.create(
            product=self.product,
            property=self.brand_property,
            value_select=self.brand_value,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
            title="Main Image",
        )

        MediaProductThrough.objects.create(
            product=self.product,
            media=self.media,
            sales_channel=self.sales_channel,
            is_main_image=True,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_check_template_mutation_success(self):
        response = self.strawberry_test_client(
            query=CHECK_TEMPLATE_MUTATION,
            variables={
                "salesChannel": {"id": self.to_global_id(self.sales_channel)},
                "template": "<section>{{ title }} - {{ brand }}</section>",
                "language": self.multi_tenant_company.language,
                "product": {"id": self.to_global_id(self.product)},
            },
        )

        self.assertIsNone(response.errors)
        data = response.data["checkSalesChannelContentTemplate"]
        self.assertTrue(data["isValid"])
        self.assertIn("Sample Product", data["renderedContent"])
        self.assertIn("brand", data["availableVariables"])
        self.assertEqual(data["errors"], [])

    def test_check_template_mutation_without_template_preserves_html(self):
        ProductTranslation.objects.filter(
            product=self.product,
            language=self.multi_tenant_company.language,
        ).update(description="<p><strong>Rendered</strong> description</p>")

        response = self.strawberry_test_client(
            query=CHECK_TEMPLATE_MUTATION,
            variables={
                "salesChannel": {"id": self.to_global_id(self.sales_channel)},
                "template": "",
                "language": self.multi_tenant_company.language,
                "product": {"id": self.to_global_id(self.product)},
            },
        )

        self.assertIsNone(response.errors)
        data = response.data["checkSalesChannelContentTemplate"]
        self.assertTrue(data["isValid"])
        self.assertIn("<p><strong>Rendered</strong> description</p>", data["renderedContent"])
        self.assertNotIn("&lt;p&gt;", data["renderedContent"])

    def test_check_template_mutation_returns_errors(self):
        response = self.strawberry_test_client(
            query=CHECK_TEMPLATE_MUTATION,
            variables={
                "salesChannel": {"id": self.to_global_id(self.sales_channel)},
                "template": "{% if title %}",
                "language": self.multi_tenant_company.language,
                "product": {"id": self.to_global_id(self.product)},
            },
        )

        self.assertIsNone(response.errors)
        data = response.data["checkSalesChannelContentTemplate"]
        self.assertFalse(data["isValid"])
        self.assertGreater(len(data["errors"]), 0)


class ResyncSalesChannelAssignsMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.view = baker.make(
            AmazonSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            is_default=True,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="SKU-1",
        )
        self.remote_product = baker.make(
            AmazonProduct,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.product,
            remote_id="ASIN-1",
            remote_sku="SKU-1",
            syncing_current_percentage=100,
        )

    @patch("sales_channels.signals.manual_sync_remote_product.send")
    def test_resync_sales_channel_view_assigns_triggers_signal(self, send_mock):
        assign = SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=self.product,
            sales_channel_view=self.view,
            remote_product=self.remote_product,
        )

        response = self.strawberry_test_client(
            query=RESYNC_SALES_CHANNEL_VIEW_ASSIGNS_MUTATION,
            variables={
                "assigns": [{"id": self.to_global_id(assign)}],
            },
        )

        self.assertIsNone(response.errors)
        self.assertEqual(len(response.data["resyncSalesChannelViewAssigns"]), 1)
        send_mock.assert_called_once()
        _, kwargs = send_mock.call_args
        self.assertEqual(kwargs["instance"].id, self.remote_product.id)
        self.assertEqual(kwargs["view"].id, self.view.id)


class ProductViewStatusMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.view = baker.make(
            AmazonSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.other_view = baker.make(
            AmazonSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
        )
        self.product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="STATUS-1",
        )
        self.other_product = baker.make(
            Product,
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            active=True,
            sku="STATUS-2",
        )
        self.inactive_sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=False,
        )
        self.inactive_view = baker.make(
            AmazonSalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.inactive_sales_channel,
        )

    def _assign_object(self, *, product, view):
        return {
            "product": {"id": self.to_global_id(product)},
            "view": {"id": self.to_global_id(view)},
        }

    def _change_status(self, *, status, product=None, view=None, asserts_errors=False):
        return self.strawberry_test_client(
            query=CHANGE_PRODUCT_VIEW_STATUS_MUTATION,
            variables={
                "status": status,
                "assignObject": self._assign_object(
                    product=product or self.product,
                    view=view or self.view,
                ),
            },
            asserts_errors=asserts_errors,
        )

    def test_change_product_view_status_to_reject_creates_rejection(self):
        response = self._change_status(status="REJECT")

        self.assertIsNone(response.errors)
        self.assertEqual(response.data["changeProductViewStatus"]["status"], "REJECT")
        self.assertEqual(response.data["changeProductViewStatus"]["createdCount"], 1)
        self.assertFalse(SalesChannelViewAssign.objects.filter(product=self.product, sales_channel_view=self.view).exists())
        self.assertTrue(RejectedSalesChannelViewAssign.objects.filter(product=self.product, sales_channel_view=self.view).exists())

    def test_change_product_view_status_to_added_replaces_rejection(self):
        RejectedSalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel_view=self.view,
            multi_tenant_company=self.multi_tenant_company,
        )

        response = self._change_status(status="ADDED")

        self.assertIsNone(response.errors)
        self.assertEqual(response.data["changeProductViewStatus"]["createdCount"], 1)
        self.assertEqual(response.data["changeProductViewStatus"]["deletedCount"], 1)
        self.assertFalse(RejectedSalesChannelViewAssign.objects.filter(product=self.product, sales_channel_view=self.view).exists())
        self.assertTrue(
            SalesChannelViewAssign.objects.filter(
                product=self.product,
                sales_channel=self.sales_channel,
                sales_channel_view=self.view,
            ).exists()
        )

    def test_change_product_view_status_to_added_for_inactive_sales_channel_raises_error(self):
        response = self._change_status(status="ADDED", view=self.inactive_view, asserts_errors=False)

        self.assertIsNotNone(response.errors)
        self.assertIn("Cannot add a product view for an inactive sales channel.", response.errors[0]["message"])
        self.assertFalse(
            SalesChannelViewAssign.objects.filter(
                product=self.product,
                sales_channel_view=self.inactive_view,
            ).exists()
        )

    def test_change_product_view_status_to_todo_removes_both_states(self):
        SalesChannelViewAssign.objects.create(
            product=self.product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            multi_tenant_company=self.multi_tenant_company,
        )
        RejectedSalesChannelViewAssign.objects.create(
            product=self.other_product,
            sales_channel_view=self.other_view,
            multi_tenant_company=self.multi_tenant_company,
        )

        added_response = self._change_status(status="REJECT")
        self.assertIsNone(added_response.errors)
        response = self._change_status(status="TODO")

        self.assertIsNone(response.errors)
        self.assertFalse(SalesChannelViewAssign.objects.filter(product=self.product, sales_channel_view=self.view).exists())
        self.assertFalse(RejectedSalesChannelViewAssign.objects.filter(product=self.product, sales_channel_view=self.view).exists())
        self.assertTrue(
            RejectedSalesChannelViewAssign.objects.filter(
                product=self.other_product,
                sales_channel_view=self.other_view,
            ).exists()
        )

    def test_change_product_views_status_accepts_per_assign_object_statuses(self):
        response = self.strawberry_test_client(
            query=CHANGE_PRODUCT_VIEWS_STATUS_MUTATION,
            variables={
                "changes": [
                    {
                        "status": "ADDED",
                        "assignObject": self._assign_object(product=self.product, view=self.view),
                    },
                    {
                        "status": "REJECT",
                        "assignObject": self._assign_object(product=self.product, view=self.other_view),
                    },
                    {
                        "status": "TODO",
                        "assignObject": self._assign_object(product=self.other_product, view=self.view),
                    },
                ],
            },
        )

        self.assertIsNone(response.errors)
        self.assertEqual(response.data["changeProductViewsStatus"]["changesCount"], 3)
        self.assertTrue(SalesChannelViewAssign.objects.filter(product=self.product, sales_channel_view=self.view).exists())
        self.assertTrue(
            RejectedSalesChannelViewAssign.objects.filter(
                product=self.product,
                sales_channel_view=self.other_view,
            ).exists()
        )
        self.assertFalse(
            SalesChannelViewAssign.objects.filter(
                product=self.other_product,
                sales_channel_view=self.view,
            ).exists()
        )
        self.assertFalse(
            RejectedSalesChannelViewAssign.objects.filter(
                product=self.other_product,
                sales_channel_view=self.view,
            ).exists()
        )

    def test_change_product_views_status_added_skips_inactive_sales_channel(self):
        response = self.strawberry_test_client(
            query=CHANGE_PRODUCT_VIEWS_STATUS_MUTATION,
            variables={
                "changes": [
                    {
                        "status": "ADDED",
                        "assignObject": self._assign_object(product=self.product, view=self.view),
                    },
                    {
                        "status": "ADDED",
                        "assignObject": self._assign_object(product=self.other_product, view=self.inactive_view),
                    },
                ],
            },
        )

        self.assertIsNone(response.errors)
        self.assertEqual(response.data["changeProductViewsStatus"]["changesCount"], 2)
        self.assertEqual(response.data["changeProductViewsStatus"]["createdCount"], 1)
        self.assertEqual(response.data["changeProductViewsStatus"]["deletedCount"], 0)
        self.assertTrue(SalesChannelViewAssign.objects.filter(product=self.product, sales_channel_view=self.view).exists())
        self.assertFalse(
            SalesChannelViewAssign.objects.filter(
                product=self.other_product,
                sales_channel_view=self.inactive_view,
            ).exists()
        )

    def test_configurable_assign_rejects_all_child_variations_for_view(self):
        parent = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            sku="STATUS-CONFIG-PARENT",
        )
        child_one = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            sku="STATUS-CONFIG-CHILD-1",
        )
        child_two = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            active=True,
            sku="STATUS-CONFIG-CHILD-2",
        )
        ConfigurableVariation.objects.create(
            parent=parent,
            variation=child_one,
            multi_tenant_company=self.multi_tenant_company,
        )
        ConfigurableVariation.objects.create(
            parent=parent,
            variation=child_two,
            multi_tenant_company=self.multi_tenant_company,
        )

        SalesChannelViewAssign.objects.create(
            product=child_one,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            multi_tenant_company=self.multi_tenant_company,
        )

        SalesChannelViewAssign.objects.create(
            product=parent,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertFalse(
            SalesChannelViewAssign.objects.filter(
                product=child_one,
                sales_channel_view=self.view,
            ).exists()
        )
        self.assertTrue(
            RejectedSalesChannelViewAssign.objects.filter(
                product=child_one,
                sales_channel_view=self.view,
            ).exists()
        )
        self.assertTrue(
            RejectedSalesChannelViewAssign.objects.filter(
                product=child_two,
                sales_channel_view=self.view,
            ).exists()
        )


class PerfectMatchMappingMutationTestCase(
    DisableMiraklConnectionMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def setUp(self):
        super().setUp()
        self.sales_channel = MiraklSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl.example.com",
            shop_id=123,
            api_key="secret",
        )

    @patch("sales_channels.integrations.mirakl.tasks.mirakl_map_perfect_match_select_values_db_task")
    def test_map_sales_channel_perfect_match_select_values_supports_mirakl(self, task_mock):
        response = self.strawberry_test_client(
            query=MAP_SALES_CHANNEL_PERFECT_MATCH_SELECT_VALUES_MUTATION,
            variables={"salesChannel": {"id": self.to_global_id(self.sales_channel)}},
        )

        self.assertIsNone(response.errors)
        self.assertTrue(response.data["mapSalesChannelPerfectMatchSelectValues"])
        task_mock.assert_called_once_with(sales_channel_id=self.sales_channel.id)

    @patch("sales_channels.integrations.mirakl.tasks.mirakl_map_perfect_match_properties_db_task")
    def test_map_sales_channel_perfect_match_properties_supports_mirakl(self, task_mock):
        response = self.strawberry_test_client(
            query=MAP_SALES_CHANNEL_PERFECT_MATCH_PROPERTIES_MUTATION,
            variables={"salesChannel": {"id": self.to_global_id(self.sales_channel)}},
        )

        self.assertIsNone(response.errors)
        self.assertTrue(response.data["mapSalesChannelPerfectMatchProperties"])
        task_mock.assert_called_once_with(sales_channel_id=self.sales_channel.id)


class CreateProductTypesFromLocalRulesMutationTestCase(
    DisableMiraklConnectionMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def _create_rule(self, *, sales_channel, value):
        product_type_property = baker.make(
            Property,
            multi_tenant_company=self.multi_tenant_company,
            is_product_type=True,
            type=Property.TYPES.SELECT,
        )
        product_type_value = baker.make(
            PropertySelectValue,
            multi_tenant_company=self.multi_tenant_company,
            property=product_type_property,
            value=value,
        )
        return baker.make(
            "properties.ProductPropertiesRule",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            product_type=product_type_value,
        )

    def _run_mutation(self, *, sales_channel):
        return self.strawberry_test_client(
            query=CREATE_SALES_CHANNEL_PRODUCT_TYPES_FROM_LOCAL_RULES_MUTATION,
            variables={"salesChannel": {"id": self.to_global_id(sales_channel)}},
        )

    def test_create_sales_channel_product_types_from_local_rules_supports_amazon(self):
        sales_channel = baker.make(
            AmazonSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        rule = self._create_rule(sales_channel=sales_channel, value="Amazon Tops")

        response = self._run_mutation(sales_channel=sales_channel)

        self.assertIsNone(response.errors)
        self.assertTrue(response.data["createSalesChannelProductTypesFromLocalRules"])
        self.assertEqual(
            AmazonProductType.objects.filter(
                sales_channel=sales_channel,
                local_instance=rule,
                multi_tenant_company=self.multi_tenant_company,
            ).count(),
            1,
        )

    def test_create_sales_channel_product_types_from_local_rules_supports_ebay(self):
        sales_channel = baker.make(
            EbaySalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        marketplace = baker.make(
            EbaySalesChannelView,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            is_default=True,
        )
        rule = self._create_rule(sales_channel=sales_channel, value="eBay Tops")

        response = self._run_mutation(sales_channel=sales_channel)

        self.assertIsNone(response.errors)
        self.assertTrue(response.data["createSalesChannelProductTypesFromLocalRules"])
        self.assertEqual(
            EbayProductType.objects.filter(
                sales_channel=sales_channel,
                local_instance=rule,
                marketplace=marketplace,
                multi_tenant_company=self.multi_tenant_company,
            ).count(),
            1,
        )

    def test_create_sales_channel_product_types_from_local_rules_supports_shein(self):
        sales_channel = baker.make(
            SheinSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        rule = self._create_rule(sales_channel=sales_channel, value="Shein Tops")

        response = self._run_mutation(sales_channel=sales_channel)

        self.assertIsNone(response.errors)
        self.assertTrue(response.data["createSalesChannelProductTypesFromLocalRules"])
        self.assertEqual(
            SheinProductType.objects.filter(
                sales_channel=sales_channel,
                local_instance=rule,
                multi_tenant_company=self.multi_tenant_company,
            ).count(),
            1,
        )

    def test_create_sales_channel_product_types_from_local_rules_supports_mirakl(self):
        sales_channel = baker.make(
            MiraklSalesChannel,
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl-product-types.example.com",
            shop_id=124,
            api_key="secret",
            active=True,
        )
        rule = self._create_rule(sales_channel=sales_channel, value="Mirakl Tops")

        response = self._run_mutation(sales_channel=sales_channel)

        self.assertIsNone(response.errors)
        self.assertTrue(response.data["createSalesChannelProductTypesFromLocalRules"])
        self.assertEqual(
            MiraklProductType.objects.filter(
                sales_channel=sales_channel,
                local_instance=rule,
                multi_tenant_company=self.multi_tenant_company,
            ).count(),
            1,
        )
