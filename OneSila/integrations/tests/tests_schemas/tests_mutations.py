from django.test import TransactionTestCase

from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin
from integrations.models import PublicIntegrationType, PublicIssueRequest
from integrations.tests.helpers import PublicIssueSchemaMixin


class PublicIssueRequestMutationTests(
    PublicIssueSchemaMixin,
    TransactionTestCaseMixin,
    TransactionTestCase,
):
    def test_create_public_issue_request(self):
        mutation = """
        mutation CreatePublicIssueRequest($data: PublicIssueRequestInput!) {
          createPublicIssueRequest(data: $data) {
            id
            integrationType {
              key
            }
            issue
            description
            submissionId
            productSku
            status
          }
        }
        """
        integration_type = PublicIntegrationType.objects.create(
            key="ebay_public_issue_request_mutation_test",
            type="ebay",
            category=PublicIntegrationType.CATEGORY_MARKETPLACE,
        )

        response = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "integrationType": {"id": self.to_global_id(integration_type)},
                    "issue": "The integration log says SKU TEST-1 failed validation.",
                    "description": "It happened while syncing an Ebay listing.",
                    "submissionId": "SUBMISSION-1",
                    "productSku": "TEST-1",
                }
            },
        )

        self.assertIsNone(response.errors)
        payload = response.data["createPublicIssueRequest"]
        self.assertEqual(payload["integrationType"]["key"], integration_type.key)
        self.assertEqual(payload["productSku"], "TEST-1")
        self.assertEqual(payload["status"], PublicIssueRequest.NEW)
        self.assertEqual(PublicIssueRequest.objects.count(), 1)

        request = PublicIssueRequest.objects.get()
        self.assertEqual(request.status, PublicIssueRequest.NEW)
        self.assertEqual(request.integration_type, integration_type)
        self.assertEqual(request.multi_tenant_company, self.multi_tenant_company)
        self.assertEqual(request.created_by_multi_tenant_user, self.user)
