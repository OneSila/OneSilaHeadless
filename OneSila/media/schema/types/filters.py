from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin

from media.models import Media, Image, Video, MediaProductThrough, File
from products.schema.types.filters import ProductFilter


@filter(Media)
class MediaFilter(SearchFilterMixin):
    search: str | None
    id: auto
    type: auto
    product: ProductFilter


@filter(Image)
class ImageFilter(SearchFilterMixin):
    search: str | None
    id: auto
    image_type: auto
    product: ProductFilter


@filter(File)
class FileFilter(SearchFilterMixin):
    search: str | None
    id: auto
    product: ProductFilter


@filter(Video)
class VideoFilter(SearchFilterMixin):
    search: str | None
    id: auto
    product: ProductFilter


@filter(MediaProductThrough)
class MediaProductThroughFilter:
    id: auto
