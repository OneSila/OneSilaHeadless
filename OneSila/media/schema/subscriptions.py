from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from media.models import Media, Image, Video, File
from media.schema.types.types import MediaType, ImageType, VideoType, FileType


@type(name="Subscription")
class MediaSubscription:
    @subscription
    async def media(self, info: Info, pk: str) -> AsyncGenerator[MediaType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Media):
            yield i

    @subscription
    async def image(self, info: Info, pk: str) -> AsyncGenerator[ImageType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Image):
            yield i

    @subscription
    async def file(self, info: Info, pk: str) -> AsyncGenerator[FileType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=File):
            yield i

    @subscription
    async def video(self, info: Info, pk: str) -> AsyncGenerator[VideoType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Video):
            yield i
