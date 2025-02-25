from decimal import Decimal

from strawberry.relay.utils import to_base64
from contacts.schema.types.types import CompanyType
from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, Annotated, lazy

from typing import List, Optional

from media.models import Media
from products.models import Product, BundleProduct, ConfigurableProduct, SimpleProduct, \
    ProductTranslation, ConfigurableVariation, BundleVariation
from taxes.schema.types.types import VatRateType
from .filters import ProductFilter, BundleProductFilter, ConfigurableProductFilter, \
    SimpleProductFilter, ProductTranslationFilter, ConfigurableVariationFilter, BundleVariationFilter
from .ordering import ProductOrder, BundleProductOrder, ConfigurableProductOrder, \
    SimpleProductOrder, ProductTranslationOrder, ConfigurableVariationOrder, BundleVariationOrder


@type(Product, filters=ProductFilter, order=ProductOrder, pagination=True, fields="__all__")
class ProductType(relay.Node, GetQuerysetMultiTenantMixin):
    vat_rate: Optional[VatRateType]
    inspector: Optional[Annotated['InspectorType', lazy('products_inspector.schema.types.types')]]

    @field()
    def proxy_id(self, info) -> str:
        if self.is_simple():
            graphql_type = SimpleProductType
        elif self.is_bundle():
            graphql_type = BundleProductType
        elif self.is_configurable():
            graphql_type = ConfigurableProductType
        else:
            graphql_type = ProductType

        return to_base64(graphql_type, self.pk)

    @field()
    def name(self, info) -> str | None:
        return self.name

    @field(description="Gets the URL of the first MediaProductThrough Image with the lowest sort order")
    def thumbnail_url(self, info) -> str | None:
        media_relation = self.mediaproductthrough_set.filter(media__type=Media.IMAGE, is_main_image=True)

        first_media = media_relation.first()
        if first_media and first_media.media.image:
            return first_media.media.image_web_url

        return None

    @field()
    def inspector_status(self, info) -> int:
        """
        Status Codes:
        0 - Green: No missing information and no missing optional information.
        1 - Orange: No missing information but missing optional information.
        2 - Red: Missing information (regardless of optional information).
        """
        if self.inspector.has_missing_information:
            return 3  # Red
        elif self.inspector.has_missing_optional_information:
            return 2  # Orange
        else:
            return 1  # Green


@type(ProductTranslation, filters=ProductTranslationFilter, order=ProductTranslationOrder, pagination=True, fields="__all__")
class ProductTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(BundleProduct, filters=BundleProductFilter, order=BundleProductOrder, pagination=True, fields="__all__")
class BundleProductType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(ConfigurableProduct, filters=ConfigurableProductFilter, order=ConfigurableProductOrder, pagination=True, fields="__all__")
class ConfigurableProductType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(SimpleProduct, filters=SimpleProductFilter, order=SimpleProductOrder, pagination=True, fields="__all__")
class SimpleProductType(relay.Node, GetQuerysetMultiTenantMixin):
    @field()
    def name(self, info) -> str | None:
        return self.name


@type(ConfigurableVariation, filters=ConfigurableVariationFilter, order=ConfigurableVariationOrder, pagination=True, fields="__all__")
class ConfigurableVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    parent: Optional[ProductType]
    variation: Optional[ProductType]


@type(BundleVariation, filters=BundleVariationFilter, order=BundleVariationOrder, pagination=True, fields="__all__")
class BundleVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    parent: Optional[ProductType]
    variation: Optional[ProductType]