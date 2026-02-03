from core.tests import TestCase
from eancodes.models import EanCode
from media.models import Media, MediaProductThrough
from products.models import Product
from sales_channels.factories.task_queue import TaskTarget
from sales_channels.integrations.amazon.factories.task_queue import AmazonProductEanCodeAddTask
from sales_channels.integrations.amazon.models import AmazonProduct, AmazonSalesChannel
from sales_channels.integrations.magento2.factories.task_queue import MagentoProductEanCodeAddTask
from sales_channels.integrations.magento2.tests.mixins import MagentoSalesChannelTestMixin
from sales_channels.integrations.magento2.factories.task_queue import MagentoProductImagesAddTask
from sales_channels.integrations.magento2.models import MagentoEanCode, MagentoProduct, MagentoSalesChannel


class MagentoImagesGuardTests(MagentoSalesChannelTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="IMG-GUARD",
        )
        self.remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.IMAGE,
        )

    def _get_target(self):
        return TaskTarget(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )

    def test_guard_allows_when_local_instance_missing(self):
        task_runner = MagentoProductImagesAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            media_product_through_id=None,
        )
        task_runner.set_local_instance()
        result = task_runner.guard(target=self._get_target())
        self.assertTrue(result.allowed)

    def test_guard_blocks_when_local_sales_channel_mismatch(self):
        other_channel = MagentoSalesChannel.objects.create(
            hostname="https://magento-other.example.com",
            host_api_username="api-user",
            host_api_key="api-key",
            authentication_method=MagentoSalesChannel.AUTH_METHOD_CHOICES[0][0],
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        mpt = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=self.media,
            sales_channel=other_channel,
        )
        task_runner = MagentoProductImagesAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            media_product_through_id=mpt.id,
        )
        task_runner.set_local_instance()
        result = task_runner.guard(target=self._get_target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "image_sales_channel_mismatch")

    def test_guard_allows_when_local_sales_channel_matches(self):
        mpt = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=self.media,
            sales_channel=self.sales_channel,
        )
        task_runner = MagentoProductImagesAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            media_product_through_id=mpt.id,
        )
        task_runner.set_local_instance()
        result = task_runner.guard(target=self._get_target())
        self.assertTrue(result.allowed)

    def test_guard_blocks_when_default_has_channel_override(self):
        default_mpt = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=self.media,
            sales_channel=None,
        )
        MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=self.media,
            sales_channel=self.sales_channel,
        )
        task_runner = MagentoProductImagesAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            media_product_through_id=default_mpt.id,
        )
        task_runner.set_local_instance()
        result = task_runner.guard(target=self._get_target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "image_sales_channel_override_exists")

    def test_guard_allows_when_default_has_no_channel_override(self):
        default_mpt = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=self.media,
            sales_channel=None,
        )
        task_runner = MagentoProductImagesAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            media_product_through_id=default_mpt.id,
        )
        task_runner.set_local_instance()
        result = task_runner.guard(target=self._get_target())
        self.assertTrue(result.allowed)


class ProductEanCodeGuardTests(MagentoSalesChannelTestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="EAN-GUARD",
        )
        self.remote_product = MagentoProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )

    def _get_target(self, *, sales_channel, remote_product):
        return TaskTarget(
            sales_channel=sales_channel,
            remote_product=remote_product,
        )

    def _build_task(self):
        return MagentoProductEanCodeAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
        )

    def test_guard_blocks_when_ean_missing(self):
        task_runner = self._build_task()
        result = task_runner.guard(
            target=self._get_target(
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            )
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "ean_code_missing")

    def test_guard_blocks_when_remote_matches(self):
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )
        MagentoEanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            sales_channel=self.remote_product.sales_channel,
            ean_code="1234567890123",
        )
        task_runner = self._build_task()
        result = task_runner.guard(
            target=self._get_target(
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            )
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "ean_code_unchanged")

    def test_guard_updates_remote_when_different(self):
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )
        remote_ean = MagentoEanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_product=self.remote_product,
            sales_channel=self.remote_product.sales_channel,
            ean_code="0000000000000",
        )
        task_runner = self._build_task()
        result = task_runner.guard(
            target=self._get_target(
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            )
        )
        self.assertTrue(result.allowed)
        remote_ean.refresh_from_db()
        self.assertEqual(remote_ean.ean_code, "1234567890123")

    def test_guard_allows_when_remote_missing(self):
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )
        task_runner = self._build_task()
        result = task_runner.guard(
            target=self._get_target(
                sales_channel=self.sales_channel,
                remote_product=self.remote_product,
            )
        )
        self.assertTrue(result.allowed)

    def test_guard_blocks_on_amazon(self):
        amazon_channel = AmazonSalesChannel.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            remote_id="AMZ-TEST",
        )
        amazon_remote = AmazonProduct.objects.create(
            sales_channel=amazon_channel,
            local_instance=self.product,
        )
        EanCode.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            ean_code="1234567890123",
        )
        task_runner = AmazonProductEanCodeAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
        )
        result = task_runner.guard(
            target=self._get_target(
                sales_channel=amazon_channel,
                remote_product=amazon_remote,
            )
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "ean_update_not_supported")
