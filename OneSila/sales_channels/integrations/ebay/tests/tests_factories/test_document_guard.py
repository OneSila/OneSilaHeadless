from core.tests import TestCase
from media.models import DocumentType, Media, MediaProductThrough
from products.models import Product
from sales_channels.factories.task_queue import TaskTarget
from sales_channels.integrations.amazon.tests.helpers import DisableWooCommerceSignalsMixin
from sales_channels.integrations.ebay.factories.task_queue import EbayProductDocumentsAddTask
from sales_channels.integrations.ebay.models import (
    EbayDocumentType,
    EbayProduct,
    EbaySalesChannel,
    EbaySalesChannelView,
)


class EbayProductDocumentGuardTests(DisableWooCommerceSignalsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.sales_channel = EbaySalesChannel.objects.create(
            hostname="https://ebay-doc-guard.example.com",
            multi_tenant_company=self.multi_tenant_company,
            active=True,
        )
        self.view = EbaySalesChannelView.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_id="EBAY_US",
            name="US",
        )
        self.product = Product.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Product.SIMPLE,
            sku="EBAY-DOC-GUARD",
        )
        self.remote_product = EbayProduct.objects.create(
            sales_channel=self.sales_channel,
            local_instance=self.product,
        )
        self.document_type = DocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            name="Certificate of Conformity",
            code="CERTIFICATE_OF_CONFORMITY",
        )
        self.media = Media.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            type=Media.FILE,
            document_type=self.document_type,
        )
        self.media_through = MediaProductThrough.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            media=self.media,
            sales_channel=None,
        )

    def _target(self):
        return TaskTarget(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
            sales_channel_view=self.view,
        )

    def _task(self):
        task = EbayProductDocumentsAddTask(
            task_func=lambda *args, **kwargs: None,
            product=self.product,
            media_product_through_id=self.media_through.id,
            number_of_remote_requests=0,
        )
        task.set_local_instance()
        return task

    def test_ebay_document_guard_blocks_when_document_type_not_mapped(self):
        task = self._task()
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "ebay_document_type_not_mapped")

    def test_ebay_document_guard_allows_when_document_type_is_mapped(self):
        EbayDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.document_type,
            remote_id="CERTIFICATE_OF_CONFORMITY",
            name="Certificate of Conformity",
        )
        task = self._task()
        result = task.guard(target=self._target())
        self.assertTrue(result.allowed)

    def test_ebay_document_guard_blocks_when_mapping_has_no_remote_id(self):
        EbayDocumentType.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=self.sales_channel,
            local_instance=self.document_type,
            remote_id="",
            name="Certificate of Conformity",
        )
        task = self._task()
        result = task.guard(target=self._target())
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "ebay_document_type_not_mapped")
