from core.schema.core.queries import node, connection, DjangoListConnection, type
from typing import List

from .types.types import MediaType, ImageType, VideoType, MediaProductThroughType, FileType


@type(name="Query")
class MediaQuery:
    media: MediaType = node()
    medias: DjangoListConnection[MediaType] = connection()

    image: ImageType = node()
    images: DjangoListConnection[ImageType] = connection()

    file: FileType = node()
    files: DjangoListConnection[FileType] = connection()

    video: VideoType = node()
    videos: DjangoListConnection[VideoType] = connection()

    media_product_through: MediaProductThroughType = node()
    media_product_throughs: DjangoListConnection[MediaProductThroughType] = connection()
