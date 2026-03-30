from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from model_bakery import baker
from unittest.mock import patch

from core.tests import TestCase
from notifications.models import CollaborationEntry, CollaborationMention, CollaborationThread, Notification


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
