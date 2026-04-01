from django.test import TransactionTestCase
from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from notifications.models import Notification, CollaborationEntry, CollaborationMention, CollaborationThread


OPEN_NOTIFICATION_MUTATION = """
mutation($id: GlobalID!) {
  openNotification(data: {id: $id}) {
    id
    opened
    url
  }
}
"""

MARK_ALL_NOTIFICATIONS_AS_VIEW_MUTATION = """
mutation {
  markAllNotificationsAsView
}
"""


CREATE_COLLABORATION_ENTRY_MUTATION = """
mutation(
  $targetId: GlobalID!,
  $mentionedUserIds: [GlobalID!],
  $comment: String
) {
  createCollaborationEntry(
    data: {
      targetId: $targetId,
      type: "COMMENT",
      comment: $comment,
      url: "/products/abc",
      mentionedUserIds: $mentionedUserIds
    }
  ) {
    id
    type
    comment
    thread {
      id
      url
    }
    createdByMultiTenantUser {
      id
    }
    mentions {
      user {
        id
      }
    }
  }
}
"""


class NotificationsMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_open_notification_marks_notification_opened(self):
        notification = baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=self.user,
            type="GENERIC",
            title="Sync done",
            url="/redirect",
            opened=False,
        )

        response = self.strawberry_test_client(
            query=OPEN_NOTIFICATION_MUTATION,
            variables={"id": self.to_global_id(notification)},
            asserts_errors=False,
        )

        self.assertIsNone(response.errors)
        notification.refresh_from_db()
        self.assertTrue(notification.opened)
        self.assertTrue(response.data["openNotification"]["opened"])
        self.assertEqual(response.data["openNotification"]["url"], "/redirect")

    def test_open_notification_rejects_other_users_notification(self):
        other_user = baker.make(
            "core.MultiTenantUser",
            multi_tenant_company=self.multi_tenant_company,
        )
        notification = baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=other_user,
            type="GENERIC",
            title="Private",
        )

        response = self.strawberry_test_client(
            query=OPEN_NOTIFICATION_MUTATION,
            variables={"id": self.to_global_id(notification)},
            asserts_errors=False,
        )

        self.assertIsNotNone(response.errors)

    def test_mark_all_notifications_as_view_marks_only_current_users_unopened_notifications(self):
        already_opened = baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=self.user,
            type="GENERIC",
            title="Already opened",
            opened=True,
        )
        first_unopened = baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=self.user,
            type="GENERIC",
            title="First unopened",
            opened=False,
        )
        second_unopened = baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=self.user,
            type="GENERIC",
            title="Second unopened",
            opened=False,
        )
        other_user = baker.make(
            "core.MultiTenantUser",
            multi_tenant_company=self.multi_tenant_company,
        )
        other_notification = baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=other_user,
            type="GENERIC",
            title="Other user unopened",
            opened=False,
        )

        response = self.strawberry_test_client(
            query=MARK_ALL_NOTIFICATIONS_AS_VIEW_MUTATION,
            asserts_errors=False,
        )

        self.assertIsNone(response.errors)
        self.assertTrue(response.data["markAllNotificationsAsView"])
        already_opened.refresh_from_db()
        first_unopened.refresh_from_db()
        second_unopened.refresh_from_db()
        other_notification.refresh_from_db()
        self.assertTrue(already_opened.opened)
        self.assertTrue(first_unopened.opened)
        self.assertTrue(second_unopened.opened)
        self.assertFalse(other_notification.opened)


class CollaborationMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.product = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=self.multi_tenant_company,
        )
        self.mentioned_user = baker.make(
            "core.MultiTenantUser",
            multi_tenant_company=self.multi_tenant_company,
        )

    def test_create_collaboration_entry_creates_thread_entry_and_mentions(self):
        response = self.strawberry_test_client(
            query=CREATE_COLLABORATION_ENTRY_MUTATION,
            variables={
                "targetId": self.to_global_id(self.product),
                "mentionedUserIds": [self.to_global_id(self.mentioned_user)],
                "comment": "Please review",
            },
            asserts_errors=False,
        )

        self.assertIsNone(response.errors)
        self.assertEqual(CollaborationThread.objects.count(), 1)
        self.assertEqual(CollaborationEntry.objects.count(), 1)
        self.assertEqual(CollaborationMention.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(response.data["createCollaborationEntry"]["thread"]["url"], "/products/abc")
        self.assertEqual(
            response.data["createCollaborationEntry"]["mentions"][0]["user"]["id"],
            self.to_global_id(self.mentioned_user),
        )
        notification = Notification.objects.get(user=self.mentioned_user)
        self.assertEqual(notification.type, Notification.TYPE_COLLABORATION_MENTION)
        self.assertEqual(notification.url, "/products/abc")

    def test_create_collaboration_entry_rejects_cross_tenant_target(self):
        other_company = baker.make("core.MultiTenantCompany")
        other_product = baker.make(
            "products.Product",
            type="SIMPLE",
            multi_tenant_company=other_company,
        )

        response = self.strawberry_test_client(
            query=CREATE_COLLABORATION_ENTRY_MUTATION,
            variables={
                "targetId": self.to_global_id(other_product),
                "comment": "Blocked",
            },
            asserts_errors=False,
        )

        self.assertIsNotNone(response.errors)
        self.assertEqual(CollaborationEntry.objects.count(), 0)

    def test_create_collaboration_entry_rejects_cross_tenant_mentions(self):
        other_company = baker.make("core.MultiTenantCompany")
        outside_user = baker.make(
            "core.MultiTenantUser",
            multi_tenant_company=other_company,
        )

        response = self.strawberry_test_client(
            query=CREATE_COLLABORATION_ENTRY_MUTATION,
            variables={
                "targetId": self.to_global_id(self.product),
                "mentionedUserIds": [self.to_global_id(outside_user)],
                "comment": "Blocked mention",
            },
            asserts_errors=False,
        )

        self.assertIsNotNone(response.errors)
        self.assertEqual(CollaborationEntry.objects.count(), 0)

    def test_create_collaboration_entry_requires_comment_for_comment_type(self):
        response = self.strawberry_test_client(
            query=CREATE_COLLABORATION_ENTRY_MUTATION,
            variables={
                "targetId": self.to_global_id(self.product),
                "comment": "",
            },
            asserts_errors=False,
        )

        self.assertIsNotNone(response.errors)
        self.assertEqual(CollaborationEntry.objects.count(), 0)
