from core.schema.types.types import auto
from core.schema.types.filters import filter

from media.models import Media, Image, Video
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
