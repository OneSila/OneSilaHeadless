from core.schema.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from media.models import Media, Image, Video
from .filters import MediaFilter, ImageFilter, VideoFilter
from .ordering import MediaOrder, ImageOrder, VideoFilter


@type(Media, filters=MediaFilter, order=MediaOrder, pagination=True, fields="__all__")
class MediaType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(Image, filters=ImageFilter, order=ImageOrder, pagination=True, fields="__all__")
class ImageType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(Video, filters=VideoFilter, order=VideoOrder, pagination=True, fields="__all__")
class VideoType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
