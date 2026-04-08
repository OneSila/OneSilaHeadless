from unittest.mock import patch

from django.db.models.signals import post_delete

from core.signals import post_create, post_update
from core.tests import TestCase
from media.models import DocumentType, Media, MediaProductThrough
from products.models import ConfigurableProduct, SimpleProduct
from products_inspector.constants import (
    OPTIONAL_DOCUMENT_TYPES_ERROR,
    REQUIRED_DOCUMENT_TYPES_ERROR,
)
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinDocumentType,
    SheinProductCategory,
    SheinSalesChannel,
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
            required_categories=["cat-shared"],
            optional_categories=[],
        )
        RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=optional_document_type,
            required_categories=[],
            optional_categories=["cat-shared"],
        )

        RemoteProductCategory.objects.create(
            product=product,
            sales_channel=self.sales_channel,
            remote_id="cat-shared",
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

    def test_shein_non_uploadable_document_types_are_ignored_by_required_block(self):
        sales_channel = SheinSalesChannel.objects.create(
            hostname="https://shein.example.com",
            open_key_id="open-key",
            secret_key="secret-key",
            multi_tenant_company=self.multi_tenant_company,
        )
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = DocumentType.objects.create(
            name="External SHEIN Cert",
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinCategory.objects.create(
            sales_channel=sales_channel,
            remote_id="cat-shein",
            name="Shein Category",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinDocumentType.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=document_type,
            remote_id="340",
            uploadable=False,
            required_categories=["cat-shein"],
            optional_categories=[],
        )
        SheinProductCategory.objects.create(
            product=product,
            sales_channel=sales_channel,
            remote_id="cat-shein",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        required_block = product.inspector.blocks.get(error_code=REQUIRED_DOCUMENT_TYPES_ERROR)
        required_block.refresh_from_db()
        self.assertTrue(required_block.successfully_checked)

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

    def test_unrelated_create_delete_signals_do_not_hit_remote_product_category_receivers(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )

        with patch(
            "products_inspector.receivers._refresh_document_type_blocks_for_products",
        ) as mock_refresh:
            post_create.send(sender=product.__class__, instance=product)
            post_delete.send(sender=product.__class__, instance=product)

        mock_refresh.assert_not_called()

    @patch("products_inspector.tasks.products_inspector__tasks__refresh_document_type_blocks_for_products")
    def test_remote_document_type_update_queues_document_block_refresh(self, mock_refresh_task):
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
        mock_refresh_task.assert_called_once_with(
            multi_tenant_company_id=self.multi_tenant_company.id,
            product_ids=[product.id],
        )

        mock_refresh_task.reset_mock()

        remote_document_type.required_categories = []
        remote_document_type.save()
        mock_refresh_task.assert_not_called()

        remote_document_type.local_instance = document_type
        remote_document_type.required_categories = ["cat-update"]
        remote_document_type.save()
        mock_refresh_task.assert_called_once_with(
            multi_tenant_company_id=self.multi_tenant_company.id,
            product_ids=[product.id],
        )

    @patch("products_inspector.tasks.products_inspector__tasks__refresh_document_type_blocks_for_products")
    def test_remote_document_type_category_changes_queue_old_and_new_products(self, mock_refresh_task):
        first_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        second_product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = DocumentType.objects.create(
            name="Category Move Cert",
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_document_type = RemoteDocumentType.objects.create(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=document_type,
            required_categories=["cat-old"],
            optional_categories=[],
        )
        RemoteProductCategory.objects.create(
            product=first_product,
            sales_channel=self.sales_channel,
            remote_id="cat-old",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )
        RemoteProductCategory.objects.create(
            product=second_product,
            sales_channel=self.sales_channel,
            remote_id="cat-new",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )

        remote_document_type.required_categories = ["cat-new"]
        remote_document_type.save()

        mock_refresh_task.assert_called_once()
        self.assertEqual(
            set(mock_refresh_task.call_args.kwargs["product_ids"]),
            {first_product.id, second_product.id},
        )
        self.assertEqual(
            mock_refresh_task.call_args.kwargs["multi_tenant_company_id"],
            self.multi_tenant_company.id,
        )

    def test_unrelated_update_signals_do_not_hit_document_type_receivers(self):
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )

        with patch(
            "products_inspector.receivers._refresh_document_type_blocks_for_products",
            side_effect=AssertionError("document type receivers should not run for unrelated senders"),
        ) as mock_refresh:
            post_update.send(sender=product.__class__, instance=product)

        mock_refresh.assert_not_called()

    def test_shein_document_type_update_skips_live_refresh_while_channel_importing(self):
        sales_channel = SheinSalesChannel.objects.create(
            hostname="https://shein.example.com",
            active=False,
            is_importing=True,
            multi_tenant_company=self.multi_tenant_company,
            secret_key="secret",
            open_key_id="open",
        )
        SheinCategory.objects.create(
            sales_channel=sales_channel,
            remote_id="cat-shein-import",
            name="Category",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = DocumentType.objects.create(
            name="Shein Import Guard Cert",
            multi_tenant_company=self.multi_tenant_company,
        )
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinProductCategory.objects.create(
            product=product,
            sales_channel=sales_channel,
            remote_id="cat-shein-import",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_document_type = SheinDocumentType.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=document_type,
            remote_id="shein-cert",
            name="Shein Cert",
            required_categories=["cat-shein-import"],
            optional_categories=[],
        )

        with patch(
            "products_inspector.tasks.products_inspector__tasks__refresh_document_type_blocks_for_products"
        ) as mock_refresh:
            remote_document_type.required_categories = []
            remote_document_type.save()

        mock_refresh.assert_not_called()

    def test_shein_document_type_update_refreshes_live_when_not_importing(self):
        sales_channel = SheinSalesChannel.objects.create(
            hostname="https://shein-live.example.com",
            active=False,
            is_importing=False,
            multi_tenant_company=self.multi_tenant_company,
            secret_key="secret-live",
            open_key_id="open-live",
        )
        SheinCategory.objects.create(
            sales_channel=sales_channel,
            remote_id="cat-shein-live",
            name="Category",
            is_leaf=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        document_type = DocumentType.objects.create(
            name="Shein Live Cert",
            multi_tenant_company=self.multi_tenant_company,
        )
        product = SimpleProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
        )
        SheinProductCategory.objects.create(
            product=product,
            sales_channel=sales_channel,
            remote_id="cat-shein-live",
            require_view=False,
            multi_tenant_company=self.multi_tenant_company,
        )
        remote_document_type = SheinDocumentType.objects.create(
            sales_channel=sales_channel,
            multi_tenant_company=self.multi_tenant_company,
            local_instance=document_type,
            remote_id="shein-cert-live",
            name="Shein Cert",
            required_categories=["cat-shein-live"],
            optional_categories=[],
        )

        with patch(
            "products_inspector.receivers._refresh_document_type_blocks_for_products"
        ) as mock_refresh:
            remote_document_type.required_categories = []
            remote_document_type.save()

        mock_refresh.assert_called_once_with(
            product_ids={product.id},
            multi_tenant_company_id=self.multi_tenant_company.id,
            run_async=True,
        )

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
