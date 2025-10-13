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
      - title: Optional image title.
      - description: Optional image description.
      - product_data: Optional data for importing an associated product.
      - is_main_image: Optional boolean flag indicating if this is the main image (default: False).
      - sort_order: Optional integer for ordering (default: 10).

    Either image_url or image_content must be provided.
    """

    def __init__(self, data: dict, import_process=None, product=None, instance=None, sales_channel=None, create_default_assignment=False):
        super().__init__(data, import_process, instance)
        self.product = product
        self.sales_channel = sales_channel
        if self.sales_channel is None and hasattr(self.import_process, 'sales_channel'):
            self.sales_channel = getattr(self.import_process, 'sales_channel')
        self.create_default_assignment = create_default_assignment

        self.set_field_if_exists('image_url')
        self.set_field_if_exists('image_content')
        self.set_field_if_exists('type', default_value=Image.PACK_SHOT)
        self.set_field_if_exists('title')
        self.set_field_if_exists('description')
        self.set_field_if_exists('product_data')

        # relevant only if we have either product or product_data provided
        self.set_field_if_exists('is_main_image', default_value=False)
        self.set_field_if_exists('sort_order', default_value=10)

        self.validate()

        self.kwargs = {}
        self.skip_create = False

        self.media_assign = None
        self.default_media_assign = None

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
        # @TODO: Temporary remove unitl we decide
        # if not self.image_url.startswith("https://"):
        #     self.skip_create = True
        #     return None

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

        if hasattr(self, 'title'):
            self.kwargs['title'] = self.title

        if hasattr(self, 'description'):
            self.kwargs['description'] = self.description

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

    def _update_media_assign_fields(self, media_assign):
        to_save = False

        for field in self.updatable_fields:
            if hasattr(self, field):
                new_value = getattr(self, field)
            else:
                new_value = getattr(media_assign, field)

            if getattr(media_assign, field) != new_value:
                setattr(media_assign, field, new_value)
                to_save = True

        if to_save:
            media_assign.save()

    def process_logic(self):

        self.instance = None
        if not self.skip_create and 'image' in self.kwargs:
            self.instance, _ = Image.objects.get_or_create(**self.kwargs)

    def post_process_logic(self):

        if self.instance is None:
            return

        if self.product is None and self.product_import_instance is not None:
            self.product_import_instance.process()
            self.product = self.product_import_instance.instance

        if self.product:
            defaults = {
                'sort_order': getattr(self, 'sort_order', 10),
                'is_main_image': getattr(self, 'is_main_image', False),
            }

            assignment_kwargs = {
                'multi_tenant_company': self.multi_tenant_company,
                'product': self.product,
                'media': self.instance,
                'sales_channel': self.sales_channel,
            }

            self.media_assign, _ = MediaProductThrough.objects.get_or_create(
                defaults=defaults,
                **assignment_kwargs,
            )
            self._update_media_assign_fields(self.media_assign)

            if self.sales_channel is not None and self.create_default_assignment:
                default_assignment_kwargs = assignment_kwargs.copy()
                default_assignment_kwargs['sales_channel'] = None

                self.default_media_assign, _ = MediaProductThrough.objects.get_or_create(
                    defaults=defaults,
                    **default_assignment_kwargs,
                )
                self._update_media_assign_fields(self.default_media_assign)
