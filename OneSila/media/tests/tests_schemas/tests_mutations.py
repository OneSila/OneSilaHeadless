from django.test import TransactionTestCase
from unittest.mock import patch, Mock
import base64
from media.models import Image, DocumentType
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class UploadImagesFromUrlsTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_upload_images_from_urls(self):
        url = "https://example.com/test.png"
        mutation = """
            mutation($imageUrls: [ImageUrlInput!]!) {
              uploadImagesFromUrls(urls: $imageUrls) { id }
            }
        """
        img_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=")
        mock_response = Mock()
        mock_response.iter_content = lambda chunk_size: [img_data]
        mock_response.headers = {"Content-Type": "image/png"}
        mock_response.raise_for_status = lambda: None
        with patch("imports_exports.factories.media.requests.get", return_value=mock_response):
            resp = self.strawberry_test_client(query=mutation, variables={"imageUrls": [{"url": url, "type": Image.PACK_SHOT}]})
        self.assertIsNone(resp.errors)
        self.assertEqual(len(resp.data["uploadImagesFromUrls"]), 1)
        self.assertEqual(Image.objects.filter(owner=self.user).count(), 1)


class DocumentTypeMutationTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_create_document_type(self):
        mutation = """
            mutation ($data: DocumentTypeInput!) {
              createDocumentType(data: $data) {
                id
                name
                code
                description
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "name": "User Manual",
                    "description": "Main usage guide",
                }
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["createDocumentType"]
        self.assertEqual(payload["name"], "User Manual")
        self.assertEqual(payload["code"], "USER_MANUAL")
        self.assertEqual(payload["description"], "Main usage guide")

    def test_update_document_type_name_and_description(self):
        document_type = DocumentType.objects.create(
            name="User Manual",
            description="Legacy description",
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($data: DocumentTypePartialInput!) {
              updateDocumentType(data: $data) {
                id
                name
                code
                description
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "id": self.to_global_id(document_type),
                    "name": "Updated User Manual",
                    "description": "Updated description",
                }
            },
        )

        self.assertIsNone(resp.errors)
        payload = resp.data["updateDocumentType"]
        self.assertEqual(payload["name"], "Updated User Manual")
        self.assertEqual(payload["description"], "Updated description")
        self.assertEqual(payload["code"], "USER_MANUAL")

    def test_update_document_type_rejects_code_field(self):
        document_type = DocumentType.objects.create(
            name="User Manual",
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($data: DocumentTypePartialInput!) {
              updateDocumentType(data: $data) {
                id
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={
                "data": {
                    "id": self.to_global_id(document_type),
                    "code": "MALICIOUS_OVERRIDE",
                }
            },
            asserts_errors=False,
        )

        self.assertIsNotNone(resp.errors)

    def test_delete_document_type(self):
        document_type = DocumentType.objects.create(
            name="Temporary certificate",
            multi_tenant_company=self.multi_tenant_company,
        )

        mutation = """
            mutation ($data: NodeInput!) {
              deleteDocumentType(data: $data) {
                id
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={"data": {"id": self.to_global_id(document_type)}},
        )

        self.assertIsNone(resp.errors)
        self.assertEqual(resp.data["deleteDocumentType"]["id"], self.to_global_id(document_type))
        self.assertFalse(DocumentType.objects.filter(id=document_type.id).exists())

    def test_delete_internal_document_type_fails(self):
        internal_document_type = DocumentType.objects.get(
            multi_tenant_company=self.multi_tenant_company,
            code=DocumentType.INTERNAL_CODE,
        )

        mutation = """
            mutation ($data: NodeInput!) {
              deleteDocumentType(data: $data) {
                id
              }
            }
        """
        resp = self.strawberry_test_client(
            query=mutation,
            variables={"data": {"id": self.to_global_id(internal_document_type)}},
            asserts_errors=False,
        )

        self.assertIsNotNone(resp.errors)
