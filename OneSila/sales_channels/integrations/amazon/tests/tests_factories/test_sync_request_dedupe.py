from unittest.mock import patch

from core.tests import TestCase
from integrations.helpers import get_import_path
from products.models import Product
from properties.models import ProductProperty, Property, ProductPropertiesRuleItem
from sales_channels import signals as sc_signals
from sales_channels.models import SalesChannelViewAssign, SyncRequest
from sales_channels.integrations.amazon.factories.task_queue import (
    AmazonProductPropertyAddTask,
    AmazonProductUpdateAddTask,
)
from sales_channels.integrations.amazon.models import AmazonProduct, AmazonSalesChannel, AmazonSalesChannelView
from sales_channels.integrations.amazon.models import AmazonProductType, AmazonProductTypeItem, AmazonProperty
from sales_channels.integrations.amazon.tasks_receiver_audit import (
    amazon__product_property__update_db_task,
    amazon__product__update_db_task,
)
from sales_channels.tests.tests_receivers.mixins import AddTaskSyncRequestTestMixin


class AmazonSyncRequestDedupeTests(AddTaskSyncRequestTestMixin, TestCase):
    """
    Dedupe scenarios for marketplace sync requests (Amazon, non-live).

    Step 1 (same remote product + view):
    - Non-product pending exists => upgrade to product, skip current and existing non-product pending.
    - No non-product pending => create non-product pending or product pending as-is.

    Step 2 (only for product):
    - If variation has siblings => escalate to parent product request and skip siblings.
    """

    def setUp(self):
        super().setUp()
        self._create_product_signal_patcher = patch.object(
            sc_signals.create_remote_product,
            "send",
            return_value=[],
        )
        self._create_product_signal_patcher.start()
        self.addCleanup(self._create_product_signal_patcher.stop)

        self.sales_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="SELLER",
        )
        self.view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW",
        )
        self._rule_initialized = False
        self._property_by_product: dict[int, ProductProperty] = {}

    def _ensure_rule_and_mapping(self, *, product: Product) -> bool:
        if self._rule_initialized:
            return False

        self.product = product
        self._init_product_rule()
        self._property = Property.objects.create(
            type=Property.TYPES.INT,
            multi_tenant_company=self.multi_tenant_company,
        )
        self._add_rule_item(property_obj=self._property)
        self._amazon_property = AmazonProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self._property,
            remote_id="AMZ-PROP",
            name="Amazon Prop",
        )
        amazon_rule = AmazonProductType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.rule,
            product_type_code="TYPE-A",
        )
        AmazonProductTypeItem.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            amazon_rule=amazon_rule,
            remote_property=self._amazon_property,
            local_instance=ProductPropertiesRuleItem.objects.filter(
                rule=self.rule,
                property=self._property,
            ).first(),
        )
        self._rule_initialized = True
        return True

    def _attach_product_type(self, *, product: Product) -> None:
        ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=self.product_type_property,
            value_select=self.product_type_value,
        )

    def _create_product_setup(self, *, sku: str):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku=sku,
        )
        initialized = self._ensure_rule_and_mapping(product=product)
        if not initialized:
            self._attach_product_type(product=product)
        remote_product = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        remote_product.successfully_created = True
        remote_product.save(update_fields=["successfully_created"])
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=remote_product,
        )
        return product, remote_product

    def _get_product_property(self, *, product: Product) -> ProductProperty:
        existing = self._property_by_product.get(product.id)
        if existing:
            return existing
        product_property = ProductProperty.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            property=self._property,
            value_int=1,
        )
        self._property_by_product[product.id] = product_property
        return product_property

    def _run_property_task(self, *, product: Product, mark_done=False):
        product_property = self._get_product_property(product=product)

        if mark_done:
            self._mark_sync_requests_done()

        task_runner = AmazonProductPropertyAddTask(
            task_func=amazon__product_property__update_db_task,
            product=product,
            product_property=product_property,
            number_of_remote_requests=0,
        )
        task_runner.run()

    def _run_product_task(self, *, product: Product):
        task_runner = AmazonProductUpdateAddTask(
            task_func=amazon__product__update_db_task,
            product=product,
            number_of_remote_requests=0,
        )
        task_runner.run()

    def _get_requests(
        self,
        *,
        remote_product: AmazonProduct,
        sync_type: str | None = None,
        task_func=None,
    ):
        queryset = SyncRequest.objects.filter(
            remote_product=remote_product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
        )
        if sync_type:
            queryset = queryset.filter(sync_type=sync_type)
        if task_func:
            queryset = queryset.filter(task_func_path=get_import_path(task_func))

        return queryset.order_by("id")

    def test_no_pending_non_product_creates_pending_non_product(self):
        """Step 1.3: No non-product pending + incoming non-product => create pending non-product."""
        product, remote_product = self._create_product_setup(sku="AMZ-NP-1")

        self._run_property_task(product=product, mark_done=True)

        requests = self._get_requests(
            remote_product=remote_product,
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_func=amazon__product_property__update_db_task,
        )
        self.assertEqual(requests.count(), 1)
        self.assertEqual(requests.first().status, SyncRequest.STATUS_PENDING)

    def test_no_pending_non_product_creates_pending_product(self):
        """Step 1.3: No non-product pending + incoming product => create pending product."""
        product, remote_product = self._create_product_setup(sku="AMZ-P-1")

        self._run_product_task(product=product)

        requests = self._get_requests(remote_product=remote_product, sync_type=SyncRequest.TYPE_PRODUCT)
        self.assertEqual(requests.count(), 1)
        self.assertEqual(requests.first().status, SyncRequest.STATUS_PENDING)

    def test_non_product_pending_upgrades_to_product_and_skips(self):
        """Step 1.2: Non-product pending exists, no product pending => create product + skip others."""
        product, remote_product = self._create_product_setup(sku="AMZ-UP-1")

        self._run_property_task(product=product)
        self._run_property_task(product=product)

        product_requests = self._get_requests(remote_product=remote_product, sync_type=SyncRequest.TYPE_PRODUCT)
        property_requests = self._get_requests(remote_product=remote_product,
                                               sync_type=SyncRequest.TYPE_PROPERTY,
                                               task_func=amazon__product_property__update_db_task,)

        self.assertEqual(product_requests.count(), 1)
        self.assertEqual(product_requests.first().status, SyncRequest.STATUS_PENDING)

        self.assertEqual(property_requests.count(), 2)
        for req in property_requests:
            self.assertEqual(req.status, SyncRequest.STATUS_SKIPPED)
            self.assertEqual(req.skipped_for_id, product_requests.first().id)

    def test_non_product_pending_with_existing_product_uses_existing(self):
        """Step 1.2: Non-product pending + product pending => skip to existing product."""
        product, remote_product = self._create_product_setup(sku="AMZ-UP-2")

        self._run_product_task(product=product)
        self._run_property_task(product=product)
        self._run_property_task(product=product)

        product_requests = self._get_requests(remote_product=remote_product, sync_type=SyncRequest.TYPE_PRODUCT)
        property_requests = self._get_requests(remote_product=remote_product, sync_type=SyncRequest.TYPE_PROPERTY)

        self.assertEqual(product_requests.count(), 1)
        self.assertEqual(product_requests.first().status, SyncRequest.STATUS_PENDING)

        for req in property_requests:
            self.assertEqual(req.status, SyncRequest.STATUS_SKIPPED)
            self.assertEqual(req.skipped_for_id, product_requests.first().id)

    def test_product_pending_exists_incoming_non_product_skips(self):
        """Step 1.3: Product pending only + incoming non-product => create skipped non-product."""
        product, remote_product = self._create_product_setup(sku="AMZ-P-2")

        self._run_product_task(product=product)
        self._run_property_task(product=product)

        product_requests = self._get_requests(remote_product=remote_product, sync_type=SyncRequest.TYPE_PRODUCT)
        property_requests = self._get_requests(
            remote_product=remote_product,
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_func=amazon__product_property__update_db_task,
        )

        self.assertEqual(product_requests.count(), 1)
        self.assertEqual(product_requests.first().status, SyncRequest.STATUS_PENDING)
        self.assertEqual(property_requests.count(), 1)
        self.assertEqual(property_requests.first().status, SyncRequest.STATUS_SKIPPED)
        self.assertEqual(property_requests.first().skipped_for_id, product_requests.first().id)

    def test_product_pending_exists_incoming_product_reuses(self):
        """Step 1.3: Product pending only + incoming product => reuse pending product."""
        product, remote_product = self._create_product_setup(sku="AMZ-P-3")

        self._run_product_task(product=product)
        self._run_product_task(product=product)

        product_requests = self._get_requests(remote_product=remote_product, sync_type=SyncRequest.TYPE_PRODUCT)
        self.assertEqual(product_requests.count(), 1)
        self.assertEqual(product_requests.first().status, SyncRequest.STATUS_PENDING)

    def test_product_variation_escalates_to_parent(self):
        """Step 2: Variation with siblings => create parent product request and skip variation."""
        parent = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="AMZ-PARENT",
        )
        self._ensure_rule_and_mapping(product=parent)
        variation_1 = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="AMZ-VAR-1",
        )
        self._attach_product_type(product=variation_1)
        variation_2 = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="AMZ-VAR-2",
        )
        self._attach_product_type(product=variation_2)

        parent_remote = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=parent,
        )
        parent_remote.successfully_created = True
        parent_remote.save(update_fields=["successfully_created"])
        variation_remote_1 = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=variation_1,
            is_variation=True,
            remote_parent_product=parent_remote,
        )
        variation_remote_1.successfully_created = True
        variation_remote_1.save(update_fields=["successfully_created"])
        AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=variation_2,
            is_variation=True,
            remote_parent_product=parent_remote,
        )
        AmazonProduct.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=variation_2,
        ).update(successfully_created=True)

        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=variation_1,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=variation_remote_1,
        )

        self._run_product_task(product=variation_1)

        parent_requests = self._get_requests(remote_product=parent_remote, sync_type=SyncRequest.TYPE_PRODUCT)
        variation_requests = self._get_requests(remote_product=variation_remote_1, sync_type=SyncRequest.TYPE_PRODUCT)

        self.assertEqual(parent_requests.count(), 1)
        self.assertEqual(parent_requests.first().status, SyncRequest.STATUS_PENDING)
        self.assertEqual(variation_requests.count(), 1)
        self.assertEqual(variation_requests.first().status, SyncRequest.STATUS_SKIPPED)
        self.assertEqual(variation_requests.first().skipped_for_id, parent_requests.first().id)

    def test_product_variation_uses_existing_parent_request(self):
        """Step 2: Parent product pending exists => skip variation to parent."""
        parent = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="AMZ-PARENT-EX",
        )
        self._ensure_rule_and_mapping(product=parent)
        variation_1 = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="AMZ-VAR-EX-1",
        )
        self._attach_product_type(product=variation_1)
        variation_2 = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="AMZ-VAR-EX-2",
        )
        self._attach_product_type(product=variation_2)

        parent_remote = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=parent,
        )
        parent_remote.successfully_created = True
        parent_remote.save(update_fields=["successfully_created"])
        variation_remote_1 = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=variation_1,
            is_variation=True,
            remote_parent_product=parent_remote,
        )
        variation_remote_1.successfully_created = True
        variation_remote_1.save(update_fields=["successfully_created"])
        AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=variation_2,
            is_variation=True,
            remote_parent_product=parent_remote,
        )
        AmazonProduct.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=variation_2,
        ).update(successfully_created=True)

        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=parent,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=parent_remote,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=variation_1,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=variation_remote_1,
        )

        self._run_product_task(product=parent)
        self._run_product_task(product=variation_1)

        parent_requests = self._get_requests(remote_product=parent_remote, sync_type=SyncRequest.TYPE_PRODUCT)
        variation_requests = self._get_requests(remote_product=variation_remote_1, sync_type=SyncRequest.TYPE_PRODUCT)

        self.assertEqual(parent_requests.count(), 1)
        self.assertEqual(parent_requests.first().status, SyncRequest.STATUS_PENDING)
        self.assertEqual(variation_requests.count(), 1)
        self.assertEqual(variation_requests.first().status, SyncRequest.STATUS_SKIPPED)
        self.assertEqual(variation_requests.first().skipped_for_id, parent_requests.first().id)

    def test_view_isolated_dedupe(self):
        """Step 1: Dedupe is scoped by view (no cross-view effects)."""
        product, remote_product = self._create_product_setup(sku="AMZ-VIEW-1")
        other_view = AmazonSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="VIEW-2",
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            sales_channel=self.sales_channel,
            sales_channel_view=other_view,
            remote_product=remote_product,
        )

        self._run_property_task(product=product, mark_done=True)

        view_one_requests = SyncRequest.objects.filter(
            remote_product=remote_product,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_func_path=get_import_path(amazon__product_property__update_db_task)
        )
        view_two_requests = SyncRequest.objects.filter(
            remote_product=remote_product,
            sales_channel=self.sales_channel,
            sales_channel_view=other_view,
            sync_type=SyncRequest.TYPE_PROPERTY,
            task_func_path=get_import_path(amazon__product_property__update_db_task)
        )

        self.assertEqual(view_one_requests.count(), 1)
        self.assertEqual(view_two_requests.count(), 1)

    def test_variation_property_double_escalation_to_parent(self):
        """Step 1 + Step 2: Two variations each get property requests -> all skipped, parent pending."""
        parent = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.CONFIGURABLE,
            sku="AMZ-PARENT-DOUBLE",
        )
        self._ensure_rule_and_mapping(product=parent)
        variation_1 = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="AMZ-VAR-DOUBLE-1",
        )
        self._attach_product_type(product=variation_1)
        variation_2 = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="AMZ-VAR-DOUBLE-2",
        )
        self._attach_product_type(product=variation_2)

        parent_remote = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=parent,
        )
        parent_remote.successfully_created = True
        parent_remote.save(update_fields=["successfully_created"])
        variation_remote_1 = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=variation_1,
            is_variation=True,
            remote_parent_product=parent_remote,
        )
        variation_remote_1.successfully_created = True
        variation_remote_1.save(update_fields=["successfully_created"])
        variation_remote_2 = AmazonProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=variation_2,
            is_variation=True,
            remote_parent_product=parent_remote,
        )
        variation_remote_2.successfully_created = True
        variation_remote_2.save(update_fields=["successfully_created"])

        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=variation_1,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=variation_remote_1,
        )
        SalesChannelViewAssign.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=variation_2,
            sales_channel=self.sales_channel,
            sales_channel_view=self.view,
            remote_product=variation_remote_2,
        )

        self._run_property_task(product=variation_1)
        self._run_property_task(product=variation_1)
        self._run_property_task(product=variation_2)
        self._run_property_task(product=variation_2)

        parent_requests = self._get_requests(remote_product=parent_remote, sync_type=SyncRequest.TYPE_PRODUCT)
        self.assertEqual(parent_requests.count(), 1)
        self.assertEqual(parent_requests.first().status, SyncRequest.STATUS_PENDING)

        var1_property = self._get_requests(remote_product=variation_remote_1, sync_type=SyncRequest.TYPE_PROPERTY, task_func=amazon__product_property__update_db_task)
        var2_property = self._get_requests(remote_product=variation_remote_2, sync_type=SyncRequest.TYPE_PROPERTY, task_func=amazon__product_property__update_db_task)

        self.assertTrue(var1_property.exists())
        self.assertTrue(var2_property.exists())
        self.assertTrue(all(req.status == SyncRequest.STATUS_SKIPPED for req in var1_property))
        self.assertTrue(all(req.status == SyncRequest.STATUS_SKIPPED for req in var2_property))
        parent_request = parent_requests.first()
        for req in list(var1_property) + list(var2_property):
            self.assertIsNotNone(req.skipped_for_id)
            skipped_for = SyncRequest.objects.get(id=req.skipped_for_id)
            if req.sync_type == SyncRequest.TYPE_PRODUCT:
                self.assertEqual(skipped_for.id, parent_request.id)
            else:
                self.assertEqual(skipped_for.sync_type, SyncRequest.TYPE_PRODUCT)
