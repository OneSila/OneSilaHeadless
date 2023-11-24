from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter

from media.models import Media, Image, Video, MediaProductThrough
from products.schema.types.filters import ProductFilter


@filter(Media)
class MediaFilter:
    id: auto
    type: auto
    product: ProductFilter


@filter(Image)
class ImageFilter:
    id: auto
    image_type: auto
    product: ProductFilter


@filter(Video)
class VideoFilter:
    id: auto
    product: ProductFilter


@filter(MediaProductThrough)
class MediaProductThroughFilter:
    id: auto
