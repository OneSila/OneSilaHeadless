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

    file = models.FileField(_('File'),
        upload_to='files/', validators=[validate_file_extensions, no_dots_in_filename],
        null=True, blank=True)

    owner = models.ForeignKey(MultiTenantUser, on_delete=models.CASCADE)

    products = models.ManyToManyField('products.Product', through='MediaProductThrough')

    objects = models.Manager()
    videos = VideoManager()
    images = ImageManager()

    @property
    def image_web_size(self):
        return self.image_web.file.image_web.size

    def is_image(self):
        return self.type == self.IMAGE

    def is_file(self):
        return self.type == self.FILE

    def is_video(self):
        return self.type == self.VIDEO

    def image_web_url(self):
        if self.image:
            return f"{generate_absolute_url(trailing_slash=False)}{self.image_web.url}"

        return None

    def file_web_url(self):
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

    class Meta:
        ordering = ('-is_main_image', 'sort_order')
