from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin

from media.models import Media, Image, Video, MediaProductThrough, File
from products.schema.types.filters import ProductFilter


@filter(Media)
class MediaFilter(SearchFilterMixin):
    id: auto
    type: auto


@filter(Image)
class ImageFilter(SearchFilterMixin):
    id: auto
    image_type: auto


@filter(File)
class FileFilter(SearchFilterMixin):
    id: auto


@filter(Video)
class VideoFilter(SearchFilterMixin):
    id: auto


@filter(MediaProductThrough)
class MediaProductThroughFilter(ExcluideDemoDataFilterMixin):
    id: auto
    media: Optional[MediaFilter]
    product: Optional[ProductFilter]
