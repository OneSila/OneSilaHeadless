from io import BytesIO
from unittest.mock import patch

from django.core.files.base import ContentFile
from reportlab.pdfgen import canvas

from core.tests import TestCase
from media.flows import generate_document_assets_flow
from media.models import Media
from media.tests.helpers import CreateImageMixin


class DocumentAssetsFlowTestCase(CreateImageMixin, TestCase):
    def _build_pdf_bytes(self):
        output = BytesIO()
        pdf_canvas = canvas.Canvas(output)
        pdf_canvas.drawString(100, 750, "Document thumbnail test")
        pdf_canvas.showPage()
        pdf_canvas.save()
        return output.getvalue()

    def test_get_real_document_file_prefers_image_when_document_image(self):
        media = Media(
            type=Media.FILE,
            is_document_image=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        media.image.save("document_source.png", self.get_image_file("red.png"), save=False)
        media.save()

        self.assertEqual(media.get_real_document_file(), media.image_url())

    def test_document_image_thumbnail_url_falls_back_to_onesila_thumbnail_for_document_images(self):
        media = Media(
            type=Media.FILE,
            is_document_image=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        media.image.save("document_source.png", self.get_image_file("red.png"), save=False)
        media.save()

        thumbnail_url = media.document_image_thumbnail_url()
        self.assertIsNotNone(thumbnail_url)
        self.assertTrue(thumbnail_url.endswith(".jpg"))

    def test_generate_document_assets_creates_pdf_from_document_image(self):
        media = Media(
            type=Media.FILE,
            is_document_image=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        media.image.save("document_source.png", self.get_image_file("red.png"), save=False)
        media.save()
        media.file = None
        media.save(update_fields=["file"])

        generate_document_assets_flow(media_instance=media)
        media.refresh_from_db()

        self.assertTrue(bool(media.file))
        self.assertTrue(media.file.name.lower().endswith(".pdf"))

    @patch(
        "media.factories.document_assets.DocumentAssetsFactory._render_pdf_first_page_to_png_bytes"
    )
    def test_generate_document_assets_creates_pdf_thumbnail(self, render_mock):
        render_mock.return_value = self.get_image_file("red.png").read()

        media = Media.objects.create(
            type=Media.FILE,
            multi_tenant_company=self.multi_tenant_company,
        )
        media.file.save("document.pdf", ContentFile(self._build_pdf_bytes()), save=True)
        media.document_image_thumbnail = None
        media.save(update_fields=["document_image_thumbnail"])

        generate_document_assets_flow(media_instance=media)
        media.refresh_from_db()

        self.assertTrue(bool(media.document_image_thumbnail))

    @patch(
        "media.factories.document_assets.DocumentAssetsFactory._render_pdf_first_page_to_png_bytes"
    )
    def test_generate_document_assets_skips_pdf_thumbnail_for_document_images(self, render_mock):
        media = Media(
            type=Media.FILE,
            is_document_image=True,
            multi_tenant_company=self.multi_tenant_company,
        )
        media.image.save("document_source.png", self.get_image_file("red.png"), save=False)
        media.save()
        media.document_image_thumbnail = None
        media.save(update_fields=["document_image_thumbnail"])

        generate_document_assets_flow(media_instance=media)
        media.refresh_from_db()

        self.assertFalse(bool(media.document_image_thumbnail))
        render_mock.assert_not_called()
