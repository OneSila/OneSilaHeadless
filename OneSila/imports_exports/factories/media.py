from imports_exports.factories.mixins import AbstractImportInstance
from media.models import Image, Media, MediaProductThrough
import base64
import os
import requests
from tempfile import NamedTemporaryFile
from django.core.files import File
from django.core.files.base import ContentFile


class ImportImageInstance(AbstractImportInstance):
    """
    Import instance for Image.

    Expected data keys:
      - image_url: HTTPS URL of the image (used if image_content is not provided).
      - image_content: Binary or base64 image content (takes priority over image_url).
      - type: Image type; defaults to Image.PACK_SHOT if not provided.
      - product_data: Optional data for importing an associated product.
      - is_main_image: Optional boolean flag indicating if this is the main image (default: False).
      - sort_order: Optional integer for ordering (default: 10).

    Either image_url or image_content must be provided.
    """

    def __init__(self, data: dict, import_process=None, product=None):
        super().__init__(data, import_process)
        self.product = product

        self.set_field_if_exists('image_url')
        self.set_field_if_exists('image_content')
        self.set_field_if_exists('type', default_value=Image.PACK_SHOT)
        self.set_field_if_exists('product_data')

        # relevant only if we have either product or product_data provided
        self.set_field_if_exists('is_main_image', default_value=False)
        self.set_field_if_exists('sort_order', default_value=10)

        self.validate()

        self.kwargs = {}
        self.skip_create = False

        self._set_product_import_instance()

    def validate(self):
        """
        Validates that at least one of 'image_url' or 'image_content' is provided.
        """
        if not (hasattr(self, 'image_url') or hasattr(self, 'image_content')):
            raise ValueError("Either 'image_url' or 'image_content' must be provided.")

    @property
    def updatable_fields(self):
        return ['sort_order', 'is_main_image']

    def _set_product_import_instance(self):
        from .products import ImportProductInstance

        self.product_import_instance = None
        if not self.product and hasattr(self, 'product_data'):
            self.product_import_instance = ImportProductInstance(self.product_data, self.import_process)

    def download_image_from_url(self):
        """
        Securely downloads an image from the given HTTPS URL.
        Returns a temporary file object if successful; otherwise, returns None.
        """
        if not self.image_url.startswith("https://"):
            self.skip_create = True
            return None
        try:
            response = requests.get(self.image_url, stream=True, timeout=10)
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                return None

            temp_file = NamedTemporaryFile(delete=True)
            for chunk in response.iter_content(chunk_size=1024):
                temp_file.write(chunk)
            temp_file.flush()
            return temp_file

        except requests.RequestException:
            self.skip_create = True
            return None

    def pre_process_logic(self):

        self.kwargs = {
            'multi_tenant_company': self.multi_tenant_company,
            'image_type': self.type,
        }

        try:
            if hasattr(self, 'image_content'):
                filename = os.path.basename(self.image_url) if hasattr(self, 'image_url') else "uploaded_image"
                file_content = ContentFile(base64.b64decode(self.image_content), name=filename)
                self.kwargs['image'] = file_content
            else:
                temp_file = self.download_image_from_url()

                if temp_file:
                    filename = os.path.basename(self.image_url)
                    django_file = File(temp_file, name=filename)
                    self.kwargs['image'] = django_file

        except Exception:
            self.skip_create = True

    def process_logic(self):

        self.instance = None
        if not self.skip_create:
            self.instance = Image.objects.create(**self.kwargs)

    def post_process_logic(self):

        if self.instance is None:
            return

        if self.product is None and self.product_import_instance is not None:
            self.product_import_instance.process()
            self.product = self.product_import_instance.instance

        if self.product:
            self.media_assign, created = MediaProductThrough.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                product=self.product,
                media=self.instance,
            )

            if not created:

                to_save = False
                for field in self.updatable_fields:
                    current_value = getattr(self.media_assign, field)
                    new_value = getattr(self.media_assign, field)
                    if current_value != new_value:
                        setattr(self.media_assign, field, new_value)
                        to_save = True

                if to_save:
                    self.media_assign.save()
