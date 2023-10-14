from core import models
from django.utils.translation import gettext_lazy as _
from core.models import MultiTenantAwareMixin

from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit

from .validators import no_dots_in_filename, validate_image_extension
from .helpers import get_media_folder_upload_path, is_landscape
from .image_specs import ImageWebSpec
from .managers import ImageManager, VideoManager


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

    MEDIA_TYPE_CHOICES = (
        (IMAGE, _('Image')),
        (VIDEO, _('Video'))
    )

    type = models.CharField(max_length=5, choices=MEDIA_TYPE_CHOICES)

    video_url = models.URLField()

    image_type = models.CharField(max_length=4, choices=IMAGE_TYPE_CHOICES, default=PACK_SHOT)
    image = models.ImageField(_('Image (High resolution)'),
        upload_to=get_media_folder_upload_path, validators=[validate_image_extension])

    image_web = ImageSpecField(source='image',
        id='mediapp:image:imagewebspec')

    products = models.ManyToManyField('products.Product', through='MediaProductThrough')
    # symmetrical=False,
    # blank=True,
    # related_name='bundles')

    objects = models.Manager()
    videos = VideoManager()
    images = ImageManager()

    @property
    def image_web_size(self):
        return self.image_web.file.image_web.size

    def __str__(self):
        return self.image.name

    def __url__(self):
        from django.conf import settings

        url = 'https://{}{}{}'.format(
            settings.DOMAIN_PRODUCTION[-1],  # Not sure how to identify the current host.  So take the production one for now.
            settings.MEDIA_URL,
            self.image.name)
        return url


class Image(Media):
    objects = ImageManager()

    class Meta:
        proxy = True


class Video(Media):
    objects = VideoManager()

    class Meta:
        proxy = True


class MediaProductThrough(models.Model):
    '''Assign an image to a product,and set its sorting-order '''
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=10)
    is_main_image = models.BooleanField(default=False)

    def __str__(self):
        return '{} > {}'.format(self.product, self.image)

    class Meta:
        ordering = ('-is_main_image', 'sort_order')
