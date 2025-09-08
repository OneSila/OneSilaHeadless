from django.test import TransactionTestCase
from unittest.mock import patch, Mock
import base64
from media.models import Image
from core.tests.tests_schemas.tests_queries import TransactionTestCaseMixin


class UploadImagesFromUrlsTestCase(TransactionTestCaseMixin, TransactionTestCase):
    def test_upload_images_from_urls(self):
        url = "https://example.com/test.png"
        mutation = """
            mutation($urls: [String!]!) {
              uploadImagesFromUrls(urls: $urls) { id }
            }
        """
        img_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=")
        mock_response = Mock()
        mock_response.iter_content = lambda chunk_size: [img_data]
        mock_response.headers = {"Content-Type": "image/png"}
        mock_response.raise_for_status = lambda: None
        with patch("imports_exports.factories.media.requests.get", return_value=mock_response):
            resp = self.strawberry_test_client(query=mutation, variables={"urls": [url]})
        self.assertIsNone(resp.errors)
        self.assertEqual(len(resp.data["uploadImagesFromUrls"]), 1)
        self.assertEqual(Image.objects.filter(owner=self.user).count(), 1)
