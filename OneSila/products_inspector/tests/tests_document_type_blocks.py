from unittest.mock import patch

from core.tests import TestCase
from media.models import DocumentType, Media, MediaProductThrough
from products.models import ConfigurableProduct, SimpleProduct
from products_inspector.constants import (
    OPTIONAL_DOCUMENT_TYPES_ERROR,
    REQUIRED_DOCUMENT_TYPES_ERROR,
)
from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
from sales_channels.models.documents import RemoteDocumentType
from sales_channels.models.products import RemoteProductCategory


class InspectorDocumentTypeBlocksTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.connect_patcher = patch(
            "sales_channels.integrations.woocommerce.models.WoocommerceSalesChannel.connect",
            lambda self, **kwargs: None,
        )
        self.connect_patcher.start()
        self.addCleanup(self.connect_patcher.stop)

        self.sales_channel = WoocommerceSalesChannel.objects.create(
            hostname="https://example.com",
            api_key="key",
            api_secret="secret",
            api_version=WoocommerceSalesChannel.API_VERSION_3,
            timeout=5,
            active=False,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _assign_document(self, *, product, document_type, sales_channel=None):
        media = Media.objects.create(
            type=Media.FILE,
            document_type=document_type,
            multi_tenant_company=self.multi_tenant_company,
        )
        MediaProductThrough.objects.create(
            product=product,
            media=media,
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_required_and_optional_document_blocks(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        required_document_type = DocumentType.objects.create(
            name="Required Cert",
            multi_tenant_company=self.multi_tenant_company,
        )
        optional_document_type = DocumentType.objects.create(
            name="Optional Cert",
            multi_tenant_company=self.multi_tenant_company,
        )

        RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=required_document_type,
            required_categories=["cat-required"],
            optional_categories=[],
        )
        RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=optional_document_type,
            required_categories=[],
            optional_categories=["cat-optional"],
        )

        RemoteProductCategory.objects.create(
            product=product,
            sales_channel=self.sales_channel,
            remote_id="cat-required",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteProductCategory.objects.create(
            product=product,
            sales_channel=self.sales_channel,
            remote_id="cat-optional",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        required_block = product.inspector.blocks.get(error_code=REQUIRED_DOCUMENT_TYPES_ERROR)
        optional_block = product.inspector.blocks.get(error_code=OPTIONAL_DOCUMENT_TYPES_ERROR)
        required_block.refresh_from_db()
        optional_block.refresh_from_db()
        self.assertFalse(required_block.successfully_checked)
        self.assertFalse(optional_block.successfully_checked)
        self.assertIn("add the following documents to the product", (required_block.fixing_message or "").lower())
        self.assertIn("add the following documents to the product", (optional_block.fixing_message or "").lower())

        self._assign_document(product=product, document_type=required_document_type)
        self._assign_document(product=product, document_type=optional_document_type)

        product.inspector.inspect_product(run_async=False)

        required_block.refresh_from_db()
        optional_block.refresh_from_db()
        self.assertTrue(required_block.successfully_checked)
        self.assertTrue(optional_block.successfully_checked)
        self.assertIsNone(required_block.fixing_message)
        self.assertIsNone(optional_block.fixing_message)

    def test_configurable_products_do_not_require_document_blocks(self):
        product = ConfigurableProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = DocumentType.objects.create(
            name="Configurable Cert",
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=document_type,
            required_categories=["cat-configurable"],
            optional_categories=[],
        )
        RemoteProductCategory.objects.create(
            product=product,
            sales_channel=self.sales_channel,
            remote_id="cat-configurable",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertFalse(
            product.inspector.blocks.filter(error_code=REQUIRED_DOCUMENT_TYPES_ERROR).exists()
        )
        self.assertFalse(
            product.inspector.blocks.filter(error_code=OPTIONAL_DOCUMENT_TYPES_ERROR).exists()
        )

    def test_remote_product_category_create_live_refreshes_document_blocks(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = DocumentType.objects.create(
            name="Live Refresh Cert",
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=document_type,
            required_categories=["cat-live"],
            optional_categories=[],
        )

        required_block = product.inspector.blocks.get(error_code=REQUIRED_DOCUMENT_TYPES_ERROR)
        required_block.refresh_from_db()
        self.assertTrue(required_block.successfully_checked)

        RemoteProductCategory.objects.create(
            product=product,
            sales_channel=self.sales_channel,
            remote_id="cat-live",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        required_block.refresh_from_db()
        self.assertFalse(required_block.successfully_checked)

    def test_remote_document_type_update_live_refreshes_document_blocks(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = DocumentType.objects.create(
            name="Mapped Cert",
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_document_type = RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=document_type,
            required_categories=["cat-update"],
            optional_categories=[],
        )
        RemoteProductCategory.objects.create(
            product=product,
            sales_channel=self.sales_channel,
            remote_id="cat-update",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        required_block = product.inspector.blocks.get(error_code=REQUIRED_DOCUMENT_TYPES_ERROR)
        required_block.refresh_from_db()
        self.assertFalse(required_block.successfully_checked)

        remote_document_type.local_instance = None
        remote_document_type.save()
        required_block.refresh_from_db()
        self.assertTrue(required_block.successfully_checked)

        remote_document_type.local_instance = document_type
        remote_document_type.required_categories = []
        remote_document_type.save()
        required_block.refresh_from_db()
        self.assertTrue(required_block.successfully_checked)

    def test_required_document_accepts_default_or_channel_document(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        required_document_type = DocumentType.objects.create(
            name="Required Cert Default Or Channel",
            multi_tenant_company=self.multi_tenant_company,
        )
        other_document_type = DocumentType.objects.create(
            name="Other Cert",
            multi_tenant_company=self.multi_tenant_company,
        )

        RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=required_document_type,
            required_categories=["cat-default-or-channel"],
            optional_categories=[],
        )
        RemoteProductCategory.objects.create(
            product=product,
            sales_channel=self.sales_channel,
            remote_id="cat-default-or-channel",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        # Add an unrelated channel-specific document.
        self._assign_document(
            product=product,
            document_type=other_document_type,
            sales_channel=self.sales_channel,
        )
        # Add required document in default scope (sales_channel=None).
        self._assign_document(
            product=product,
            document_type=required_document_type,
        )

        product.inspector.inspect_product(run_async=False)
        required_block = product.inspector.blocks.get(error_code=REQUIRED_DOCUMENT_TYPES_ERROR)
        required_block.refresh_from_db()
        self.assertTrue(required_block.successfully_checked)

    def test_media_through_create_delete_live_refreshes_document_blocks(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        required_document_type = DocumentType.objects.create(
            name="Live Media Through Cert",
            multi_tenant_company=self.multi_tenant_company,
        )

        RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=required_document_type,
            required_categories=["cat-media-live"],
            optional_categories=[],
        )
        RemoteProductCategory.objects.create(
            product=product,
            sales_channel=self.sales_channel,
            remote_id="cat-media-live",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        required_block = product.inspector.blocks.get(error_code=REQUIRED_DOCUMENT_TYPES_ERROR)
        required_block.refresh_from_db()
        self.assertFalse(required_block.successfully_checked)

        media = Media.objects.create(
            type=Media.FILE,
            document_type=required_document_type,
            multi_tenant_company=self.multi_tenant_company,
        )
        assignment = MediaProductThrough.objects.create(
            product=product,
            media=media,
            multi_tenant_company=self.multi_tenant_company,
        )
        required_block.refresh_from_db()
        self.assertTrue(required_block.successfully_checked)

        assignment.delete()
        required_block.refresh_from_db()
        self.assertFalse(required_block.successfully_checked)
