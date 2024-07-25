from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field
from strawberry_django.fields.types import DjangoImageType
from strawberry.relay.utils import to_base64
from typing import List

from media.models import Media, Image, Video, MediaProductThrough, File

from core.schema.multi_tenant.types.types import MultiTenantUserType
from products.schema.types.types import ProductType
from .filters import MediaFilter, ImageFilter, VideoFilter, \
    MediaProductThroughFilter, FileFilter
from .ordering import MediaOrder, ImageOrder, VideoOrder, \
    MediaProductThroughOrder, FileOrder


@type(Media, filters=MediaFilter, order=MediaOrder, pagination=True, fields="__all__")
class MediaType(relay.Node, GetQuerysetMultiTenantMixin):
    image_web: DjangoImageType | None
    image_web_url: str | None
    file_url: str | None
    onesila_thumbnail_url: str | None
    owner: MultiTenantUserType

    @field()
    def proxy_id(self, info) -> str:
        if self.is_image():
            graphql_type = ImageType
        elif self.is_video():
            graphql_type = VideoType
        elif self.is_file():
            graphql_type = FileType
        else:
            graphql_type = MediaType

        return to_base64(graphql_type, self.id)


@type(Image, filters=ImageFilter, order=ImageOrder, pagination=True, fields="__all__")
class ImageType(relay.Node, GetQuerysetMultiTenantMixin):
    image_web: DjangoImageType | None
    image_web_url: str | None
    image_url: str | None
    onesila_thumbnail_url: str | None
    owner: MultiTenantUserType


@type(Video, filters=VideoFilter, order=VideoOrder, pagination=True, fields="__all__")
class VideoType(relay.Node, GetQuerysetMultiTenantMixin):
    owner: MultiTenantUserType


@type(File, filters=FileFilter, order=FileOrder, pagination=True, fields="__all__")
class FileType(relay.Node, GetQuerysetMultiTenantMixin):
    owner: MultiTenantUserType
    file_url: str | None


@type(MediaProductThrough, filters=MediaProductThroughFilter,
    order=MediaProductThroughOrder, pagination=True, fields="__all__")
class MediaProductThroughType(relay.Node, GetQuerysetMultiTenantMixin):
    media: MediaType
    product: ProductType

    @field()
    def product_id(self, info) -> str:
        return to_base64(ProductType, self.product.id)

    @field()
    def active(self, info) -> str:
        return self.product.active

    @field()
    def product_type(self, info) -> str:
        return self.product.type
