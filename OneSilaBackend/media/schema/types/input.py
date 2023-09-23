from core.schema.types.types import auto
from core.schema.types.input import NodeInput, input, partial

from media.models import Media, Image, Video, MediaProductThrough


@input(Media, fields="__all__")
class MediaInput:
    pass


@partial(Media, fields="__all__")
class MediaPartialInput(NodeInput):
    pass


@input(Image, fields="__all__")
class ImageLocationInput:
    pass


@partial(Image, fields="__all__")
class ImageLocationPartialInput(NodeInput):
    pass


@input(Video, fields="__all__")
class VideoLocationInput:
    pass


@partial(Video, fields="__all__")
class VideoLocationPartialInput(NodeInput):
    pass


@input(MediaProductThrough, fields="__all__")
class MediaProductThroughInput:
    pass


@partial(MediaProductThrough, fields="__all__")
class MediaProductThroughInput(NodeInput):
    pass
