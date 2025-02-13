from core import models
from django.utils.translation import gettext_lazy as _
from core.models import MultiTenantAwareMixin, MultiTenantUser

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit

from get_absolute_url.helpers import generate_absolute_url

from core.validators import no_dots_in_filename, validate_image_extension, \
    validate_file_extensions
from .image_specs import ImageWebSpec
from .managers import ImageManager, VideoManager, FileManager


import os


##########
# Models #
##########

class Media(models.Model):
    '''
    Class to store Images
    '''
    MOOD_SHOT = 'MOOD'
    PACK_SHOT = 'PACK'

    IMAGE_TYPE_CHOICES = (
        (MOOD_SHOT, _('Mood Shot')),
        (PACK_SHOT, _('Pack Shot')),
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

    video_url = models.URLField(null=True, blank=True)

    image_type = models.CharField(max_length=4, choices=IMAGE_TYPE_CHOICES, default=PACK_SHOT)
    image = models.ImageField(_('Image (High resolution)'),
        upload_to='images/', validators=[validate_image_extension],
        null=True, blank=True)
    image_web = ImageSpecField(source='image',
        id='mediapp:image:imagewebspec')
    onesila_thumbnail = ImageSpecField(source='image',
        id='mediapp:image:onesilathumbnail')
    image_hash = models.CharField(_('image hash'), max_length=100, blank=True, null=True)

    file = models.FileField(_('File'),
        upload_to='files/', validators=[validate_file_extensions, no_dots_in_filename],
        null=True, blank=True)

    owner = models.ForeignKey(MultiTenantUser, on_delete=models.CASCADE)

    products = models.ManyToManyField('products.Product', through='MediaProductThrough')

    objects = models.Manager()
    videos = VideoManager()
    images = ImageManager()

    class Meta:
        constraints = [
            # Ensure that if image_hash is set then it is unique per multi_tenant_company.
            models.UniqueConstraint(
                fields=['multi_tenant_company', 'image_hash'],
                name='unique_image_hash_per_tenant',
                condition=models.Q(image_hash__isnull=False)
            ),
        ]

    @property
    def image_web_size(self):
        return self.image_web.file.image_web.size

    @property
    def image_web_url(self):
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


class Image(Media):
    objects = ImageManager()
    proxy_filter_fields = {'type': Media.IMAGE}

    class Meta:
        proxy = True


class Video(Media):
    objects = VideoManager()
    proxy_filter_fields = {'type': Media.VIDEO}

    class Meta:
        proxy = True


class File(Media):
    objects = FileManager()
    proxy_filter_fields = {'type': Media.FILE}

    class Meta:
        proxy = True


class MediaProductThrough(models.Model):
    '''Assign an image to a product,and set its sorting-order '''
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=10)
    is_main_image = models.BooleanField(default=False)

    def __str__(self):
        return '{} > {}'.format(self.product, self.media)

    @property
    def sales_channels_sort_order(self):
        return self.sort_order + 1 # because for some integration 0 can be a position

    class Meta:
        ordering = ('sort_order',)
        unique_together = ('product', 'media')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Ensure the first image is automatically set as the main image if none exist
        if self.media.type == Media.IMAGE:
            # Check if there's no image marked as the main image for this product
            if not MediaProductThrough.objects.filter(product=self.product, media__type=Media.IMAGE, is_main_image=True).exists():
                # Set the first image by sort order as the main image if none are set
                first_image = MediaProductThrough.objects.filter(product=self.product, media__type=Media.IMAGE).order_by('sort_order').first()
                if first_image and first_image.pk == self.pk:
                    self.is_main_image = True
                    self.save()
                elif first_image:
                    first_image.is_main_image = True
                    first_image.save()

            # If this image is marked as the main image, ensure no other image for this product is marked as main
            if self.is_main_image:
                # Get all other instances marked as main image for the same product
                other_main_images = MediaProductThrough.objects.filter(
                    product=self.product,
                    media__type=Media.IMAGE,
                    is_main_image=True
                ).exclude(pk=self.pk)

                # Iterate through each instance and set is_main_image to False, saving individually to trigger post_save
                for other in other_main_images:
                    other.is_main_image = False
                    other.save()
