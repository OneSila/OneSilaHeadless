from io import BytesIO
from pathlib import Path
import logging
import subprocess
import tempfile

from django.core.files.base import ContentFile
from PIL import Image as PILImage
from PIL import ImageFilter

logger = logging.getLogger(__name__)


class DocumentAssetsFactory:
    THUMBNAIL_MAX_WIDTH = 420
    THUMBNAIL_JPEG_QUALITY = 45
    THUMBNAIL_BLUR_RADIUS = 0.6

    def __init__(self, *, media_instance):
        self.media_instance = media_instance
        self._update_fields = set()

    def _is_file_media(self):
        return self.media_instance.type == self.media_instance.FILE

    def _is_pdf_file(self):
        if not self.media_instance.file:
            return False
        return self.media_instance.file.name.lower().endswith(".pdf")

    def _build_generated_pdf_filename(self):
        if self.media_instance.image:
            base_name = Path(self.media_instance.image.name).stem
        else:
            base_name = f"media_{self.media_instance.id}"

        return f"{base_name.replace('.', '_')}.pdf"

    def _build_thumbnail_filename(self):
        if self.media_instance.file:
            base_name = Path(self.media_instance.file.name).stem
        else:
            base_name = f"media_{self.media_instance.id}"

        return f"{base_name.replace('.', '_')}_thumbnail.jpg"

    def _generate_pdf_from_document_image(self):
        if not self.media_instance.is_document_image:
            return

        if not self.media_instance.image:
            return

        if self._is_pdf_file():
            return

        with self.media_instance.image.open("rb") as image_fp:
            with PILImage.open(image_fp) as image:
                if image.mode != "RGB":
                    image = image.convert("RGB")

                output_buffer = BytesIO()
                image.save(output_buffer, format="PDF")
                output_buffer.seek(0)

                self.media_instance.file.save(
                    self._build_generated_pdf_filename(),
                    ContentFile(output_buffer.read()),
                    save=False,
                )
                self._update_fields.add("file")

    def _render_pdf_first_page_to_png_bytes(self):
        with self.media_instance.file.open("rb") as source_file:
            pdf_bytes = source_file.read()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "source.pdf"
            output_prefix = Path(temp_dir) / "thumbnail"
            output_path = Path(f"{output_prefix}.png")

            input_path.write_bytes(pdf_bytes)
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    "1",
                    "-singlefile",
                    "-png",
                    str(input_path),
                    str(output_prefix),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            if not output_path.exists():
                return None

            with PILImage.open(output_path) as image:
                image = image.convert("RGB")

                if image.width > self.THUMBNAIL_MAX_WIDTH:
                    ratio = self.THUMBNAIL_MAX_WIDTH / image.width
                    target_height = max(1, int(image.height * ratio))
                    resampling = getattr(PILImage, "Resampling", PILImage).BILINEAR
                    image = image.resize((self.THUMBNAIL_MAX_WIDTH, target_height), resampling)

                image = image.filter(ImageFilter.GaussianBlur(radius=self.THUMBNAIL_BLUR_RADIUS))

                output_buffer = BytesIO()
                image.save(
                    output_buffer,
                    format="JPEG",
                    quality=self.THUMBNAIL_JPEG_QUALITY,
                    optimize=True,
                )
                output_buffer.seek(0)
                return output_buffer.read()

    def _generate_pdf_thumbnail(self):
        if self.media_instance.is_document_image:
            return

        if not self._is_pdf_file():
            return

        if self.media_instance.document_image_thumbnail:
            return

        try:
            png_bytes = self._render_pdf_first_page_to_png_bytes()
            if not png_bytes:
                return

            self.media_instance.document_image_thumbnail.save(
                self._build_thumbnail_filename(),
                ContentFile(png_bytes),
                save=False,
            )
            self._update_fields.add("document_image_thumbnail")
        except Exception:
            logger.exception(
                "Failed generating PDF thumbnail for media_id=%s",
                self.media_instance.id,
            )

    def _save(self):
        if not self._update_fields:
            return

        self.media_instance.save(update_fields=list(self._update_fields))

    def run(self):
        if not self._is_file_media():
            return

        try:
            self._generate_pdf_from_document_image()
            self._generate_pdf_thumbnail()
            self._save()
        except Exception:
            logger.exception(
                "Failed generating document assets for media_id=%s",
                self.media_instance.id,
            )
