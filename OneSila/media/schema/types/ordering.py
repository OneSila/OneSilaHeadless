from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from media.models import Media, Image, Video, MediaProductThrough


@order(Media)
class MediaOrder:
    id: auto
    type: auto
    product: auto


@order(Image)
class ImageOrder:
    id: auto
    image_type: auto
    product: auto


@order(Video)
class VideoOrder:
    id: auto
    image_type: auto
    product: auto


@order(MediaProductThrough)
class MediaProductThroughOrder:
    id: auto
