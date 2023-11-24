from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from media.models import Media, Image, Video, MediaProductThrough
from .filters import MediaFilter, ImageFilter, VideoFilter, \
    MediaProductThroughFilter
from .ordering import MediaOrder, ImageOrder, VideoOrder, \
    MediaProductThroughOrder


@type(Media, filters=MediaFilter, order=MediaOrder, pagination=True, fields="__all__")
class MediaType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(Image, filters=ImageFilter, order=ImageOrder, pagination=True, fields="__all__")
class ImageType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(Video, filters=VideoFilter, order=VideoOrder, pagination=True, fields="__all__")
class VideoType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(MediaProductThrough, filters=MediaProductThroughFilter,
    order=MediaProductThroughOrder, pagination=True, fields="__all__")
class MediaProductThroughType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
