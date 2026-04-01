from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from model_bakery import baker
from unittest.mock import patch

from core.tests import TestCase
from imports_exports.models import Import, MappedImport
from notifications.helpers import build_import_tab_url, build_product_tab_url, create_user_notification
from notifications.models import CollaborationEntry, CollaborationMention, CollaborationThread, Notification
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.products import RemoteProduct


class CollaborationModelTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.product = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.thread = baker.make(
            CollaborationThread,
            multi_tenant_company=self.multi_tenant_company,
            content_type=ContentType.objects.get_for_model(self.product, for_concrete_model=False),
            object_id=self.product.id,
        )

    def test_thread_is_unique_per_target_per_company(self):
        with self.assertRaises(IntegrityError):
            baker.make(
                CollaborationThread,
                multi_tenant_company=self.multi_tenant_company,
                content_type=ContentType.objects.get_for_model(self.product, for_concrete_model=False),
                object_id=self.product.id,
            )

    def test_entry_mention_is_unique_per_user(self):
        entry = baker.make(
            CollaborationEntry,
            multi_tenant_company=self.multi_tenant_company,
            thread=self.thread,
            type=CollaborationEntry.TYPE_COMMENT,
            comment="hello",
        )
        baker.make(
            CollaborationMention,
            multi_tenant_company=self.multi_tenant_company,
            entry=entry,
            user=self.user,
        )

        with self.assertRaises(IntegrityError):
            baker.make(
                CollaborationMention,
                multi_tenant_company=self.multi_tenant_company,
                entry=entry,
                user=self.user,
            )

    def test_entry_mention_user_must_match_entry_company(self):
        other_company = baker.make("core.MultiTenantCompany")
        other_user = baker.make(
            "core.MultiTenantUser",
            multi_tenant_company=other_company,
        )
        entry = baker.make(
            CollaborationEntry,
            multi_tenant_company=self.multi_tenant_company,
            thread=self.thread,
            type=CollaborationEntry.TYPE_COMMENT,
            comment="hello",
        )

        with self.assertRaises(ValidationError):
            baker.make(
                CollaborationMention,
                multi_tenant_company=self.multi_tenant_company,
                entry=entry,
                user=other_user,
            )

    @patch("notifications.receivers.refresh_subscription_receiver")
    def test_entry_mention_creates_notification_with_thread_url(self, mock_refresh_subscription_receiver):
        self.thread.url = "/products/test-thread"
        self.thread.save(update_fields=["url"])

        entry = baker.make(
            CollaborationEntry,
            multi_tenant_company=self.multi_tenant_company,
            thread=self.thread,
            type=CollaborationEntry.TYPE_COMMENT,
            comment="Please review",
            created_by_multi_tenant_user=self.user,
            last_update_by_multi_tenant_user=self.user,
        )
        mentioned_user = baker.make(
            "core.MultiTenantUser",
            multi_tenant_company=self.multi_tenant_company,
        )

        mention = baker.make(
            CollaborationMention,
            multi_tenant_company=self.multi_tenant_company,
            entry=entry,
            user=mentioned_user,
            created_by_multi_tenant_user=self.user,
            last_update_by_multi_tenant_user=self.user,
        )

        notification = Notification.objects.get(user=mentioned_user)
        self.assertEqual(notification.type, Notification.TYPE_COLLABORATION_MENTION)
        self.assertEqual(notification.url, self.thread.url)
        self.assertEqual(notification.message, "Please review")
        self.assertEqual(notification.metadata["mention_id"], mention.id)
        mock_refresh_subscription_receiver.assert_called_once_with(mentioned_user)


class NotificationReceiverTestCase(TestCase):
    def test_create_user_notification_skips_duplicate_within_one_minute(self):
        first = create_user_notification(
            user=self.user,
            notification_type=Notification.TYPE_REMOTE_PRODUCT_STATUS_CHANGED,
            title="Remote product status updated",
            message="Product SKU-1 changed to Completed.",
            url="/products/test",
            actor=self.user,
            multi_tenant_company=self.multi_tenant_company,
        )

        second = create_user_notification(
            user=self.user,
            notification_type=Notification.TYPE_REMOTE_PRODUCT_STATUS_CHANGED,
            title="Remote product status updated",
            message="Product SKU-1 changed to Completed.",
            url="/products/test",
            actor=self.user,
            multi_tenant_company=self.multi_tenant_company,
        )

        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(Notification.objects.count(), 1)

    @patch("notifications.receivers.refresh_subscription_receiver")
    def test_remote_product_status_change_creates_notification(self, mock_refresh_subscription_receiver):
        product = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
            sku="SKU-1",
        )
        sales_channel = baker.make(
            "ebay.EbaySalesChannel",
            multi_tenant_company=self.multi_tenant_company,
            hostname="ebay-test",
        )
        view = baker.make(
            "ebay.EbaySalesChannelView",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
        )
        remote_product = baker.make(
            "ebay.EbayProduct",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=product,
            status=RemoteProduct.STATUS_PROCESSING,
            syncing_current_percentage=0,
        )
        baker.make(
            SalesChannelViewAssign,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            product=product,
            remote_product=remote_product,
            created_by_multi_tenant_user=self.user,
            last_update_by_multi_tenant_user=self.user,
        )

        remote_product.status = RemoteProduct.STATUS_COMPLETED
        remote_product.syncing_current_percentage = 100
        remote_product.save(update_fields=["status", "syncing_current_percentage"], skip_status_check=False)

        notification = Notification.objects.get(
            user=self.user,
            type=Notification.TYPE_REMOTE_PRODUCT_STATUS_CHANGED,
        )
        self.assertEqual(notification.url, build_product_tab_url(product=product, tab="websites"))
        self.assertEqual(notification.message, "Product SKU-1 changed to Completed.")
        self.assertEqual(notification.metadata["status"], RemoteProduct.STATUS_COMPLETED)
        mock_refresh_subscription_receiver.assert_called_once_with(self.user)

    @patch("notifications.receivers.refresh_subscription_receiver")
    def test_remote_product_status_change_skips_notifications_while_importing(self, mock_refresh_subscription_receiver):
        product = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
            sku="SKU-2",
        )
        sales_channel = baker.make(
            "ebay.EbaySalesChannel",
            multi_tenant_company=self.multi_tenant_company,
            hostname="ebay-importing",
            is_importing=True,
        )
        view = baker.make(
            "ebay.EbaySalesChannelView",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
        )
        remote_product = baker.make(
            "ebay.EbayProduct",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=product,
            status=RemoteProduct.STATUS_PROCESSING,
        )
        baker.make(
            SalesChannelViewAssign,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            product=product,
            remote_product=remote_product,
            last_update_by_multi_tenant_user=self.user,
        )

        remote_product.status = RemoteProduct.STATUS_FAILED
        remote_product.save(update_fields=["status"], skip_status_check=False)

        self.assertFalse(
            Notification.objects.filter(type=Notification.TYPE_REMOTE_PRODUCT_STATUS_CHANGED).exists()
        )
        mock_refresh_subscription_receiver.assert_not_called()

    @patch("notifications.receivers.refresh_subscription_receiver")
    def test_remote_product_repeat_failed_status_creates_notification(self, mock_refresh_subscription_receiver):
        product = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
            sku="SKU-3",
        )
        sales_channel = baker.make(
            "ebay.EbaySalesChannel",
            multi_tenant_company=self.multi_tenant_company,
            hostname="ebay-failed-repeat",
        )
        view = baker.make(
            "ebay.EbaySalesChannelView",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
        )
        remote_product = baker.make(
            "ebay.EbayProduct",
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            local_instance=product,
            status=RemoteProduct.STATUS_FAILED,
        )
        baker.make(
            SalesChannelViewAssign,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
            sales_channel_view=view,
            product=product,
            remote_product=remote_product,
            last_update_by_multi_tenant_user=self.user,
        )

        remote_product.status = RemoteProduct.STATUS_FAILED
        remote_product.save(update_fields=["status"], skip_status_check=False)

        notification = Notification.objects.get(
            user=self.user,
            type=Notification.TYPE_REMOTE_PRODUCT_STATUS_CHANGED,
        )
        self.assertEqual(notification.message, "Product SKU-3 changed to Failed.")
        self.assertEqual(notification.metadata["status"], RemoteProduct.STATUS_FAILED)
        self.assertEqual(notification.metadata["previous_status"], RemoteProduct.STATUS_FAILED)
        mock_refresh_subscription_receiver.assert_called_once_with(self.user)

    @patch("notifications.receivers.refresh_subscription_receiver")
    def test_mapped_import_success_creates_notification_for_creator(self, mock_refresh_subscription_receiver):
        import_process = baker.make(
            MappedImport,
            multi_tenant_company=self.multi_tenant_company,
            created_by_multi_tenant_user=self.user,
            last_update_by_multi_tenant_user=self.user,
            status=Import.STATUS_PROCESSING,
            name="Mapped catalog import",
        )

        import_process.status = Import.STATUS_SUCCESS
        import_process.save(update_fields=["status"])

        notification = Notification.objects.get(
            user=self.user,
            type=Notification.TYPE_IMPORT_FINISHED,
        )
        self.assertIsNone(notification.url)
        self.assertEqual(notification.message, "Mapped catalog import is Success.")
        self.assertEqual(notification.metadata["status"], Import.STATUS_SUCCESS)
        mock_refresh_subscription_receiver.assert_called_once_with(self.user)

    @patch("notifications.receivers.refresh_subscription_receiver")
    def test_sales_channel_import_failure_uses_imports_tab_url(self, mock_refresh_subscription_receiver):
        sales_channel = baker.make(
            "mirakl.MiraklSalesChannel",
            multi_tenant_company=self.multi_tenant_company,
            hostname="mirakl-test",
            sub_type="debenhams",
        )
        import_process = baker.make(
            "mirakl.MiraklSalesChannelImport",
            multi_tenant_company=self.multi_tenant_company,
            created_by_multi_tenant_user=self.user,
            last_update_by_multi_tenant_user=self.user,
            sales_channel=sales_channel,
            status=Import.STATUS_PROCESSING,
        )

        import_process.status = Import.STATUS_FAILED
        import_process.save(update_fields=["status"])

        notification = Notification.objects.get(
            user=self.user,
            type=Notification.TYPE_IMPORT_FAILED,
        )
        self.assertEqual(notification.url, build_import_tab_url(import_process=import_process))
        self.assertIn("/integrations/mirakl/", notification.url)
        self.assertNotIn("/integrations/debenhams/", notification.url)
        self.assertEqual(notification.message, "MiraklSalesChannelImport is Failed.")
        self.assertEqual(notification.metadata["status"], Import.STATUS_FAILED)
        mock_refresh_subscription_receiver.assert_called_once_with(self.user)
