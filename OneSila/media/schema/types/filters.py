from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin

from media.models import Media, Image, Video, MediaProductThrough, File, DocumentType
from products.schema.types.filters import ProductFilter
from sales_channels.schema.types.filters import SalesChannelFilter


@filter(Media)
class MediaFilter(SearchFilterMixin):
    id: auto
    type: auto
    image_type: auto
    is_document_image: auto
    document_type: Optional['DocumentTypeFilter']
    document_language: auto

@filter(Image)
class ImageFilter(SearchFilterMixin):
    id: auto
    image_type: auto


@filter(File)
class FileFilter(SearchFilterMixin):
    id: auto
    is_document_image: auto
    document_type: Optional['DocumentTypeFilter']
    document_language: auto


@filter(Video)
class VideoFilter(SearchFilterMixin):
    id: auto


@filter(DocumentType)
class DocumentTypeFilter(SearchFilterMixin):
    id: auto
    name: auto
    code: auto
    description: auto


@filter(MediaProductThrough)
class MediaProductThroughFilter(ExcluideDemoDataFilterMixin):
    id: auto
    media: Optional[MediaFilter]
    product: Optional[ProductFilter]
    sales_channel: Optional[SalesChannelFilter]
