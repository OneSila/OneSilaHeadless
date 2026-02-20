from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from media.models import Media, Image, Video, MediaProductThrough, File, DocumentType


@order(Media)
class MediaOrder:
    id: auto
    type: auto
    product: auto
    created_at: auto
    updated_at: auto


@order(Image)
class ImageOrder:
    id: auto
    image_type: auto
    product: auto
    created_at: auto
    updated_at: auto

@order(Video)
class VideoOrder:
    id: auto
    image_type: auto
    product: auto
    created_at: auto
    updated_at: auto

@order(File)
class FileOrder:
    id: auto
    product: auto
    created_at: auto
    updated_at: auto

@order(MediaProductThrough)
class MediaProductThroughOrder:
    id: auto
    created_at: auto
    updated_at: auto

@order(DocumentType)
class DocumentTypeOrder:
    id: auto
    name: auto
    code: auto
    created_at: auto
    updated_at: auto