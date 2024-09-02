from core.schema.core.types.input import NodeInput, input, partial
from media.models import Media, Image, Video, MediaProductThrough, File


@input(Media, fields="__all__", exclude=['owner'])
class MediaInput:
    pass


@input(Media, fields="__all__", exclude=['owner'])
class MediaPartialInput(NodeInput):
    pass


@input(Image, exclude=['owner', 'type'])
class ImageInput:
    pass


@partial(Image, exclude=['owner', 'type'])
class ImagePartialInput(NodeInput):
    pass


@input(File, exclude=['owner', 'type'])
class FileInput:
    pass


@partial(File, exclude=['owner', 'type'])
class FilePartialInput(NodeInput):
    pass


@input(Video, exclude=['owner', 'type'])
class VideoInput:
    pass


@partial(Video, exclude=['owner', 'type'])
class VideoPartialInput(NodeInput):
    pass


@input(MediaProductThrough, fields="__all__")
class MediaProductThroughInput:
    pass


@partial(MediaProductThrough, fields="__all__")
class MediaProductThroughPartialInput(NodeInput):
    pass
