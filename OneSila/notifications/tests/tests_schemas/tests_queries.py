from model_bakery import baker

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from notifications.models import Notification
from django.test import TransactionTestCase


ME_NOTIFICATIONS_QUERY = """
query {
  me {
    id
    notifications {
      id
      title
      opened
    }
  }
}
"""


COLLABORATION_THREAD_BY_TARGET_QUERY = """
query($targetId: GlobalID!) {
  collaborationThreadByTarget(targetId: $targetId) {
    id
    url
    targetId
    entries {
      id
      type
      comment
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
}
"""


class NotificationsQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.notification_old = baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=self.user,
            type="GENERIC",
            title="Old",
            opened=False,
        )
        self.notification_new = baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=self.user,
            type="GENERIC",
            title="New",
            opened=True,
        )
        baker.make(
            Notification,
            multi_tenant_company=self.multi_tenant_company,
            user=baker.make(
                "core.MultiTenantUser",
                multi_tenant_company=self.multi_tenant_company,
            ),
            type="GENERIC",
            title="Other user",
        )

    def test_me_notifications_field_returns_latest_notifications(self):
        response = self.strawberry_test_client(query=ME_NOTIFICATIONS_QUERY)

        self.assertIsNone(response.errors)
        self.assertEqual(
            [item["title"] for item in response.data["me"]["notifications"]],
            ["New", "Old"],
        )


class CollaborationQueryTestCase(TransactionTestCaseMixin, TransactionTestCase):
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

        mutation = """
        mutation($targetId: GlobalID!, $mentionedUserIds: [GlobalID!]) {
          createCollaborationEntry(
            data: {
              targetId: $targetId,
              type: "COMMENT",
              comment: "Need review",
              url: "/products/1",
              mentionedUserIds: $mentionedUserIds
            }
          ) {
            id
          }
        }
        """

        response = self.strawberry_test_client(
            query=mutation,
            variables={
                "targetId": self.to_global_id(self.product),
                "mentionedUserIds": [self.to_global_id(self.mentioned_user)],
            },
            asserts_errors=False,
        )
        self.assertIsNone(response.errors)

    def test_collaboration_thread_by_target_returns_entries_and_mentions(self):
        response = self.strawberry_test_client(
            query=COLLABORATION_THREAD_BY_TARGET_QUERY,
            variables={"targetId": self.to_global_id(self.product)},
        )

        self.assertIsNone(response.errors)
        thread = response.data["collaborationThreadByTarget"]
        self.assertEqual(thread["url"], "/products/1")
        self.assertEqual(thread["targetId"], self.to_global_id(self.product))
        self.assertEqual(thread["entries"][0]["type"], "COMMENT")
        self.assertEqual(thread["entries"][0]["comment"], "Need review")
        self.assertEqual(
            thread["entries"][0]["mentions"][0]["user"]["id"],
            self.to_global_id(self.mentioned_user),
        )
