from core.schema.core.types.types import auto
from core.schema.core.types.input import NodeInput, input, partial

from media.models import Media, Image, Video, MediaProductThrough, File


@input(Media, fields="__all__")
class MediaInput:
    pass


@partial(Media, fields="__all__")
class MediaPartialInput(NodeInput):
    pass


@input(Image, fields="__all__")
class ImageInput:
    pass


@partial(Image, fields="__all__")
class ImagePartialInput(NodeInput):
    pass


@input(File, fields="__all__")
class FileInput:
    pass


@partial(File, fields="__all__")
class FilePartialInput(NodeInput):
    pass


@input(Video, fields="__all__")
class VideoInput:
    pass


@partial(Video, fields="__all__")
class VideoPartialInput(NodeInput):
    pass


@input(MediaProductThrough, fields="__all__")
class MediaProductThroughInput:
    pass


@partial(MediaProductThrough, fields="__all__")
class MediaProductThroughPartialInput(NodeInput):
    pass
