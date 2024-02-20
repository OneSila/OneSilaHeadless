from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin
from strawberry_django.fields.types import DjangoImageType

from typing import List

from media.models import Media, Image, Video, MediaProductThrough, File
from .filters import MediaFilter, ImageFilter, VideoFilter, \
    MediaProductThroughFilter, FileFilter
from .ordering import MediaOrder, ImageOrder, VideoOrder, \
    MediaProductThroughOrder, FileOrder


@type(Media, filters=MediaFilter, order=MediaOrder, pagination=True, fields="__all__")
class MediaType(relay.Node, GetQuerysetMultiTenantMixin):
    image_web: DjangoImageType | None
    image_web_url: str | None


@type(Image, filters=ImageFilter, order=ImageOrder, pagination=True, fields="__all__")
class ImageType(relay.Node, GetQuerysetMultiTenantMixin):
    image_web: DjangoImageType | None
    image_web_url: str | None


@type(Video, filters=VideoFilter, order=VideoOrder, pagination=True, fields="__all__")
class VideoType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(File, filters=FileFilter, order=FileOrder, pagination=True, fields="__all__")
class FileType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(MediaProductThrough, filters=MediaProductThroughFilter,
    order=MediaProductThroughOrder, pagination=True, fields="__all__")
class MediaProductThroughType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
