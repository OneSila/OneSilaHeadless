from core.tests import TestCase
from products.models import Product, ProductTranslation
from sales_channels.factories.task_queue import TaskTarget
from sales_channels.helpers import build_content_data, compute_content_data_hash
from sales_channels.integrations.magento2.factories.task_queue import MagentoProductContentAddTask
from sales_channels.integrations.magento2.models import (
    MagentoProduct,
    MagentoProductContent,
    MagentoSalesChannel,
)
from sales_channels.integrations.magento2.models.sales_channels import (
    MagentoRemoteLanguage,
    MagentoSalesChannelView,
)
from sales_channels.tests.helpers import DisableMagentoAndWooConnectionsMixin


class MagentoContentGuardTests(DisableMagentoAndWooConnectionsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = MagentoSalesChannel.objects.create(
            hostname="https://magento.example.com",
            host_api_username="api-user",
            host_api_key="api-key",
            authentication_method=MagentoSalesChannel.AUTH_METHOD_CHOICES[0][0],
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.sales_channel_view = MagentoSalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id=1,
            name="Default View",
        )
        MagentoRemoteLanguage.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            sales_channel_view=self.sales_channel_view,
            local_instance="en",
            remote_code="en_US",
        )

    def _get_target(self, *, remote_product):
        return TaskTarget(
            sales_channel=self.sales_channel,
            remote_product=remote_product,
        )

    def _build_task(self, *, product):
        return MagentoProductContentAddTask(
            task_func=lambda *args, **kwargs: None,
            product=product,
            number_of_remote_requests=0,
        )

    def _create_translation(self, *, product, sales_channel, name, description):
        return ProductTranslation.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=product,
            sales_channel=sales_channel,
            language="en",
            name=name,
            description=description,
        )

    def test_guard_blocks_when_content_unchanged(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONTENT-UNCHANGED",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        self._create_translation(
            product=product,
            sales_channel=None,
            name="Base Name",
            description="Base Desc",
        )

        content_data = build_content_data(product=product, sales_channel=self.sales_channel)
        content_hash = compute_content_data_hash(content_data=content_data)
        MagentoProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            content_data=content_data,
            content_data_hash=content_hash,
        )

        task_runner = self._build_task(product=product)
        result = task_runner.guard(target=self._get_target(remote_product=remote_product))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "content_unchanged")

    def test_guard_allows_when_content_changed_and_updates_remote(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONTENT-CHANGED",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        self._create_translation(
            product=product,
            sales_channel=None,
            name="New Name",
            description="New Desc",
        )
        remote_content = MagentoProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            content_data={"en-gb": {"name": "Old Name", "description": "Old Desc"}},
        )

        task_runner = self._build_task(product=product)
        result = task_runner.guard(target=self._get_target(remote_product=remote_product))
        self.assertTrue(result.allowed)
        remote_content.refresh_from_db()
        self.assertEqual(remote_content.content_data["en-gb"]["name"], "New Name")
        self.assertEqual(remote_content.content_data["en-gb"]["description"], "New Desc")

    def test_guard_allows_when_remote_missing(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONTENT-NO-REMOTE",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        self._create_translation(
            product=product,
            sales_channel=None,
            name="Name",
            description="Desc",
        )

        task_runner = self._build_task(product=product)
        result = task_runner.guard(target=self._get_target(remote_product=remote_product))
        self.assertTrue(result.allowed)
        self.assertFalse(MagentoProductContent.objects.filter(remote_product=remote_product).exists())

    def test_default_change_ignored_when_channel_specific_present(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONTENT-OVERRIDE",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        self._create_translation(
            product=product,
            sales_channel=None,
            name="Default Name",
            description="Default Desc",
        )
        self._create_translation(
            product=product,
            sales_channel=self.sales_channel,
            name="Channel Name",
            description="Channel Desc",
        )

        content_data = build_content_data(product=product, sales_channel=self.sales_channel)
        content_hash = compute_content_data_hash(content_data=content_data)
        MagentoProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            content_data=content_data,
            content_data_hash=content_hash,
        )

        default_translation = ProductTranslation.objects.get(
            product=product,
            sales_channel=None,
            language="en",
        )
        default_translation.description = "Default Desc Updated"
        default_translation.save()

        task_runner = self._build_task(product=product)
        result = task_runner.guard(target=self._get_target(remote_product=remote_product))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "content_unchanged")

    def test_irrelevant_field_change_is_ignored(self):
        product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="CONTENT-SUBTITLE",
        )
        remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=product,
        )
        translation = self._create_translation(
            product=product,
            sales_channel=None,
            name="Name",
            description="Description",
        )

        content_data = build_content_data(product=product, sales_channel=self.sales_channel)
        content_hash = compute_content_data_hash(content_data=content_data)
        MagentoProductContent.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
            content_data=content_data,
            content_data_hash=content_hash,
        )

        translation.subtitle = "New subtitle"
        translation.save()

        task_runner = self._build_task(product=product)
        result = task_runner.guard(target=self._get_target(remote_product=remote_product))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "content_unchanged")
