from core import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from core.models import MultiTenantAwareMixin, MultiTenantUser, MultiTenantCompany
from django.core.files.base import ContentFile

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit

from get_absolute_url.helpers import generate_absolute_url

from core.validators import no_dots_in_filename, validate_image_extension, \
    validate_file_extensions
from core.upload_paths import tenant_upload_to
from .image_specs import ImageWebSpec
from .managers import (
    DocumentTypeManager,
    ImageManager,
    VideoManager,
    FileManager,
    MediaManager,
    MediaProductThroughManager,
)


import os
import mimetypes

from PIL import Image as PILImage


##########
# Models #
##########

class DocumentType(models.Model):
    INTERNAL_CODE = "INTERNAL"
    INTERNAL_NAME = "Internal"
    INTERNAL_DESCRIPTION = (
        "These documents are not pushed to integrations and are only for internal team use. "
        "They are not public, are not sent anywhere, and cannot be mapped."
    )
    INTERNAL_DELETE_ERROR_MESSAGE = _("The INTERNAL document type cannot be deleted.")

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    objects = DocumentTypeManager()

    class Meta:
        search_terms = ["name", "code", "description"]
        constraints = [
            models.UniqueConstraint(
                fields=["multi_tenant_company", "code"],
                name="unique_document_type_code_per_company",
                violation_error_message=_("This document type code already exists for this company."),
            ),
        ]

    @staticmethod
    def _normalise_code(*, value: str) -> str:
        normalised = slugify(value).replace("-", "_").upper()
        return normalised or "DOCUMENT_TYPE"

    def _generate_unique_code(self):
        base_code = self._normalise_code(value=self.name)
        if not self.multi_tenant_company_id:
            return base_code

        queryset = self.__class__.objects.filter(
            multi_tenant_company_id=self.multi_tenant_company_id,
        ).exclude(id=self.id)

        code = base_code
        counter = 1
        while queryset.filter(code=code).exists():
            code = f"{base_code}_{counter}"
            counter += 1

        return code

    def save(self, *args, **kwargs):
        if self.name and not self.code:
            self.code = self._generate_unique_code()
        elif self.code:
            self.code = self._normalise_code(value=self.code)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        force_delete = kwargs.pop("force_delete", False)
        if self.code == self.INTERNAL_CODE and not force_delete:
            raise ValidationError(self.INTERNAL_DELETE_ERROR_MESSAGE)

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Media(models.Model):
    '''
    Class to store Images
    '''
    MOOD_SHOT = 'MOOD'
    PACK_SHOT = 'PACK'
    COLOR_SHOT = 'COLOR'

    IMAGE_TYPE_CHOICES = (
        (MOOD_SHOT, _('Mood Shot')),
        (PACK_SHOT, _('Pack Shot')),
        (COLOR_SHOT, _('Color Image')),
    )

    IMAGE = 'IMAGE'
    VIDEO = 'VIDEO'
    FILE = 'FILE'

    MEDIA_TYPE_CHOICES = (
        (IMAGE, _('Image')),
        (VIDEO, _('Video')),
        (FILE, _("File")),
    )

    type = models.CharField(max_length=5, choices=MEDIA_TYPE_CHOICES)
    title = models.CharField(_('title'), max_length=255, blank=True, null=True)
    description = models.TextField(_('description'), blank=True, null=True)

    # Video Fields
    video_url = models.URLField(null=True, blank=True)
    # Image Fields
    image_type = models.CharField(max_length=5, choices=IMAGE_TYPE_CHOICES, default=PACK_SHOT)
    image = models.ImageField(
        _('Image (High resolution)'),
        upload_to=tenant_upload_to('images'),
        validators=[validate_image_extension],
        null=True,
        blank=True,
    )
    image_web = ImageSpecField(source='image',
        id='mediapp:image:imagewebspec')
    onesila_thumbnail = ImageSpecField(source='image',
        id='mediapp:image:onesilathumbnail')
    shein_main_image = ImageSpecField(source='image',
        id='mediapp:image:sheinmain')
    shein_detail_image = ImageSpecField(source='image',
        id='mediapp:image:sheindetail')
    shein_square_image = ImageSpecField(source='image',
        id='mediapp:image:sheinsquare')
    shein_color_block_image = ImageSpecField(source='image',
        id='mediapp:image:sheincolorblock')
    shein_detail_page_image = ImageSpecField(source='image',
        id='mediapp:image:sheindetailpage')
    image_hash = models.CharField(_('image hash'), max_length=100, blank=True, null=True)
    # File Fields
    file = models.FileField(
        _('File'),
        upload_to=tenant_upload_to('files'),
        validators=[validate_file_extensions, no_dots_in_filename],
        null=True,
        blank=True,
    )
    is_document_image = models.BooleanField(default=False)
    document_image_thumbnail = models.ImageField(
        _('Document image thumbnail'),
        upload_to=tenant_upload_to('document_thumbnails'),
        validators=[validate_image_extension],
        null=True,
        blank=True,
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    document_language = models.CharField(
        max_length=7,
        choices=MultiTenantCompany.LANGUAGE_CHOICES,
        null=True,
        blank=True,
    )

    # can be created by the system
    owner = models.ForeignKey(MultiTenantUser, on_delete=models.CASCADE, blank=True, null=True)

    products = models.ManyToManyField('products.Product', through='MediaProductThrough')

    objects = MediaManager()
    videos = VideoManager()
    images = ImageManager()

    class Meta:
        search_terms = ['title', 'description']
        constraints = [
            # Ensure that if image_hash is set then it is unique per multi_tenant_company.
            models.UniqueConstraint(
                fields=['multi_tenant_company', 'image_hash'],
                name='unique_image_hash_per_tenant',
                condition=models.Q(image_hash__isnull=False)
            ),
            models.CheckConstraint(
                condition=models.Q(type="FILE", document_type__isnull=False) | ~models.Q(type="FILE"),
                name="media_file_requires_document_type",
                violation_error_message=_("Document type is required when media type is FILE."),
            ),
            models.CheckConstraint(
                condition=models.Q(is_document_image=False) | models.Q(type="FILE", image__isnull=False),
                name="media_document_image_requires_image",
                violation_error_message=_("Document image media must be FILE type and include an image."),
            ),
        ]

    @staticmethod
    def _mime_to_extension(*, mime_type):
        mime_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
            "image/tiff": "tiff",
            "image/bmp": "bmp",
        }
        return mime_map.get(mime_type, "jpg")

    def _detect_file_mime_type(self):
        if not self.file:
            return None

        uploaded_file = getattr(self.file, "file", None)
        content_type = getattr(uploaded_file, "content_type", None)
        if content_type:
            return content_type.lower()

        guessed, _ = mimetypes.guess_type(self.file.name or "")
        guessed = guessed.lower() if guessed else None

        try:
            with self.file.open("rb") as file_obj:
                with PILImage.open(file_obj) as image:
                    pil_mime = getattr(image, "get_format_mimetype", lambda: None)()
                    if pil_mime:
                        return pil_mime.lower()

                    if image.format:
                        mapped = PILImage.MIME.get(image.format.upper())
                        if mapped:
                            return mapped.lower()
        except Exception:
            pass

        return guessed

    def _sync_document_image_from_file(self):
        if self.type != self.FILE or not self.file:
            return

        mime_type = self._detect_file_mime_type()
        if not mime_type or not mime_type.startswith("image/"):
            return

        self.is_document_image = True

        if self.image:
            return

        with self.file.open("rb") as file_obj:
            file_bytes = file_obj.read()

        if not file_bytes:
            return

        file_base_name = os.path.splitext(os.path.basename(self.file.name or ""))[0] or "document_image"
        file_extension = self._mime_to_extension(mime_type=mime_type)
        image_filename = f"{file_base_name}.{file_extension}"
        self.image.save(image_filename, ContentFile(file_bytes), save=False)

    def clean(self):
        self._sync_document_image_from_file()
        super().clean()

        if self.type == self.FILE and not self.document_type_id:
            raise ValidationError({"document_type": _("Document type is required when media type is FILE.")})

        if self.is_document_image and self.type != self.FILE:
            raise ValidationError({"type": _("Only FILE media can be marked as document images.")})

        if self.is_document_image and not self.image:
            raise ValidationError({"image": _("Image is required when is_document_image is enabled.")})

    def save(self, *args, **kwargs):
        self._sync_document_image_from_file()

        if self.type == self.FILE and not self.document_type_id and self.multi_tenant_company_id:
            internal_document_type, _ = DocumentType.objects.create_internal_for_company(
                multi_tenant_company=self.multi_tenant_company,
            )
            self.document_type = internal_document_type

        if not self.document_language and self.multi_tenant_company_id:
            self.document_language = getattr(self.multi_tenant_company, "language", None)

        super().save(*args, **kwargs)

    @property
    def image_web_size(self):
        return self.image_web.file.image_web.size

    @property
    def image_web_url(self):
        # from django.conf import settings
        #
        # if settings.DEBUG:
        #     return 'https://images.pexels.com/photos/45201/kitty-cat-kitten-pet-45201.jpeg'

        if self.image:
            return f"{generate_absolute_url(trailing_slash=False)}{self.image_web.url}"

        return None

    def is_image(self):
        return self.type == self.IMAGE

    def is_file(self):
        return self.type == self.FILE

    def is_video(self):
        return self.type == self.VIDEO

    def onesila_thumbnail_url(self):
        if self.image:
            return f"{generate_absolute_url(trailing_slash=False)}{self.onesila_thumbnail.url}"

        return None

    def image_url(self):
        if self.image:
            return f"{generate_absolute_url(trailing_slash=False)}{self.image.url}"

        return None

    def file_url(self):
        if self.file:
            return f"{generate_absolute_url(trailing_slash=False)}{self.file.url}"

        return None

    def document_image_thumbnail_url(self):
        if self.document_image_thumbnail:
            return f"{generate_absolute_url(trailing_slash=False)}{self.document_image_thumbnail.url}"

        if self.is_document_image and self.image:
            return self.onesila_thumbnail_url()

        return None

    def get_real_document_file(self):
        if self.is_document_image and self.image:
            return self.image_url()

        return self.file_url()


class Image(Media):
    objects = ImageManager()
    proxy_filter_fields = {'type': Media.IMAGE}

    class Meta:
        proxy = True
        search_terms = ['title', 'description']


class Video(Media):
    objects = VideoManager()
    proxy_filter_fields = {'type': Media.VIDEO}

    class Meta:
        proxy = True
        search_terms = ['title', 'description']


class File(Media):
    objects = FileManager()
    proxy_filter_fields = {'type': Media.FILE}

    class Meta:
        proxy = True
        search_terms = ['title', 'description']


class MediaProductThrough(models.Model):
    '''Assign an image to a product,and set its sorting-order '''
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=10)
    is_main_image = models.BooleanField(default=False)
    sales_channel = models.ForeignKey(
        'sales_channels.SalesChannel',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='media_product_assignments',
    )

    objects = MediaProductThroughManager()

    def __str__(self):
        return '{} > {}'.format(self.product, self.media)

    @property
    def sales_channels_sort_order(self):
        return self.sort_order + 1  # because for some integration 0 can be a position

    class Meta:
        ordering = ('sort_order',)
        constraints = [
            models.UniqueConstraint(
                fields=('product', 'media'),
                condition=models.Q(sales_channel__isnull=True),
                name='media_product_unique_default_sales_channel',
            ),
            models.UniqueConstraint(
                fields=('product', 'media', 'sales_channel'),
                condition=models.Q(sales_channel__isnull=False),
                name='media_product_unique_per_sales_channel',
            ),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Ensure the first image is automatically set as the main image if none exist
        if self.media.type == Media.IMAGE:
            channel_images = MediaProductThrough.objects.get_product_images(
                product=self.product,
                sales_channel=self.sales_channel,
            )

            # Check if there's no image marked as the main image for this product
            if not channel_images.filter(is_main_image=True).exists():
                # Set the first image by sort order as the main image if none are set
                first_image = channel_images.order_by('sort_order').first()
                if first_image and first_image.pk == self.pk:
                    self.is_main_image = True
                    self.save()
                elif first_image:
                    first_image.is_main_image = True
                    first_image.save()

            # If this image is marked as the main image, ensure no other image for this product is marked as main
            if self.is_main_image:
                # Get all other instances marked as main image for the same product
                other_main_images = channel_images.filter(is_main_image=True).exclude(pk=self.pk)

                # Iterate through each instance and set is_main_image to False, saving individually to trigger post_save
                for other in other_main_images:
                    other.is_main_image = False
                    other.save()
