from core.schema.core.mutations import update, delete, type, List
from .fields import create

from ..types.types import MediaType, ImageType, VideoType, MediaProductThroughType, \
    FileType
from ..types.input import MediaInput, ImageInput, VideoInput, MediaProductThroughInput, \
    FileInput, FilePartialInput, MediaPartialInput, ImagePartialInput, \
    VideoPartialInput, MediaProductThroughPartialInput
import strawberry_django
from strawberry.types import Info
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from strawberry_django.auth.utils import get_current_user
from imports_exports.factories.media import ImportImageInstance
from types import SimpleNamespace


@type(name="Mutation")
class MediaMutation:
    create_media: MediaType = create(MediaInput)
    create_medias: List[MediaType] = create(MediaInput)
    update_media: MediaType = update(MediaPartialInput)
    delete_media: MediaType = delete()
    delete_medias: List[MediaType] = delete(is_bulk=True)

    create_image: ImageType = create(ImageInput)
    create_images: List[ImageType] = create(List[ImageInput])
    update_image: ImageType = update(ImagePartialInput)
    delete_image: ImageType = delete()
    delete_images: List[ImageType] = delete(is_bulk=True)

    create_file: FileType = create(FileInput)
    create_files: List[FileType] = create(List[FileInput])
    update_file: FileType = update(FilePartialInput)
    delete_file: FileType = delete()
    delete_files: List[FileType] = delete(is_bulk=True)

    create_video: VideoType = create(VideoInput)
    create_videos: List[VideoType] = create(List[VideoInput])
    update_video: VideoType = update(VideoPartialInput)
    delete_video: VideoType = delete()
    delete_videos: List[VideoType] = delete(is_bulk=True)

    create_mediaproducthrough: MediaProductThroughType = create(MediaProductThroughInput)
    create_mediaproducthroughs: List[MediaProductThroughType] = create(MediaProductThroughInput)
    update_mediaproducthrough: MediaProductThroughType = update(MediaProductThroughPartialInput)
    delete_mediaproducthrough: MediaProductThroughType = delete()
    delete_mediaproducthroughs: List[MediaProductThroughType] = delete()

    @strawberry_django.mutation(handle_django_errors=True, extensions=default_extensions)
    def upload_images_from_urls(self, urls: List[str], info: Info) -> List[ImageType]:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        user = get_current_user(info)
        import_process = SimpleNamespace(multi_tenant_company=multi_tenant_company)
        images = []
        for url in urls:
            importer = ImportImageInstance({'image_url': url}, import_process=import_process)
            importer.process()
            if importer.instance:
                importer.instance.owner = user
                importer.instance.save()
                images.append(importer.instance)
        return images
