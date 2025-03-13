from core.schema.core.mutations import update, delete, type, List
from .fields import create

from ..types.types import MediaType, ImageType, VideoType, MediaProductThroughType, \
    FileType
from ..types.input import MediaInput, ImageInput, VideoInput, MediaProductThroughInput, \
    FileInput, FilePartialInput, MediaPartialInput, ImagePartialInput, \
    VideoPartialInput, MediaProductThroughPartialInput


@type(name="Mutation")
class MediaMutation:
    create_media: MediaType = create(MediaInput)
    create_medias: List[MediaType] = create(MediaInput)
    update_media: MediaType = update(MediaPartialInput)
    delete_media: MediaType = delete()
    delete_medias: List[MediaType] = delete()

    create_image: ImageType = create(ImageInput)
    create_images: List[ImageType] = create(List[ImageInput])
    update_image: ImageType = update(ImagePartialInput)
    delete_image: ImageType = delete()
    delete_images: List[ImageType] = delete()

    create_file: FileType = create(FileInput)
    create_files: List[FileType] = create(List[FileInput])
    update_file: FileType = update(FilePartialInput)
    delete_file: FileType = delete()
    delete_files: List[FileType] = delete()

    create_video: VideoType = create(VideoInput)
    create_videos: List[VideoType] = create(List[VideoInput])
    update_video: VideoType = update(VideoPartialInput)
    delete_video: VideoType = delete()
    delete_videos: List[VideoType] = delete()

    create_mediaproducthrough: MediaProductThroughType = create(MediaProductThroughInput)
    create_mediaproducthroughs: List[MediaProductThroughType] = create(MediaProductThroughInput)
    update_mediaproducthrough: MediaProductThroughType = update(MediaProductThroughPartialInput)
    delete_mediaproducthrough: MediaProductThroughType = delete()
    delete_mediaproducthroughs: List[MediaProductThroughType] = delete()
