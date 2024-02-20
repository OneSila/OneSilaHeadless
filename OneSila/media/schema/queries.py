from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import MediaType, ImageType, VideoType, MediaProductThroughType, FileType


@type(name="Query")
class MediaQuery:
    media: MediaType = node()
    medias: ListConnectionWithTotalCount[MediaType] = connection()

    image: ImageType = node()
    images: ListConnectionWithTotalCount[ImageType] = connection()

    file: FileType = node()
    files: ListConnectionWithTotalCount[FileType] = connection()

    video: VideoType = node()
    videos: ListConnectionWithTotalCount[VideoType] = connection()

    media_product_through: MediaProductThroughType = node()
    media_product_throughs: ListConnectionWithTotalCount[MediaProductThroughType] = connection()
