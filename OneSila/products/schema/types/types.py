from decimal import Decimal

from strawberry.relay.utils import to_base64
from contacts.schema.types.types import CompanyType
from core.schema.core.types.types import relay, type, field, Annotated, lazy, strawberry_type
from core.schema.core.mixins import GetQuerysetMultiTenantMixin

from typing import List, Optional

from media.models import Media
from products.models import (
    Product,
    BundleProduct,
    ConfigurableProduct,
    SimpleProduct,
    ProductTranslation,
    ConfigurableVariation,
    BundleVariation,
    AliasProduct,
    ProductTranslationBulletPoint,
)
from properties.models import ProductProperty
from properties.schema.types.types import ProductPropertyType
from taxes.schema.types.types import VatRateType
from .filters import (
    ProductFilter,
    BundleProductFilter,
    ConfigurableProductFilter,
    SimpleProductFilter,
    ProductTranslationFilter,
    ConfigurableVariationFilter,
    BundleVariationFilter,
    AliasProductFilter,
    ProductTranslationBulletPointFilter,
)
from .ordering import (
    ProductOrder,
    BundleProductOrder,
    ConfigurableProductOrder,
    SimpleProductOrder,
    ProductTranslationOrder,
    ConfigurableVariationOrder,
    BundleVariationOrder,
    AliasProductOrder,
    ProductTranslationBulletPointOrder,
)


@type(Product, filters=ProductFilter, order=ProductOrder, pagination=True, fields="__all__")
class ProductType(relay.Node, GetQuerysetMultiTenantMixin):
    vat_rate: Optional[VatRateType]
    inspector: Optional[Annotated['InspectorType', lazy('products_inspector.schema.types.types')]]
    saleschannelviewassign_set: List[Annotated['SalesChannelViewAssignType', lazy("sales_channels.schema.types.types")]]
    productproperty_set: List[Annotated['ProductPropertyType', lazy("properties.schema.types.types")]]
    salesprice_set: List[Annotated['SalesPriceType', lazy("sales_prices.schema.types.types")]]
    alias_products: List[Annotated['ProductType', lazy("products.schema.types.types")]]
    alias_parent_product: Optional[Annotated['ProductType', lazy("products.schema.types.types")]]

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

    @field()
    def has_parents(self, info) -> bool:
        return ConfigurableVariation.objects.filter(variation_id=self.id).exists()


@type(ProductTranslation, filters=ProductTranslationFilter, order=ProductTranslationOrder, pagination=True, fields="__all__")
class ProductTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Optional[Annotated['SalesChannelType', lazy('sales_channels.schema.types.types')]]


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


@type(AliasProduct, filters=AliasProductFilter, order=AliasProductOrder, pagination=True, fields="__all__")
class AliasProductType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def name(self, info) -> str | None:
        return self.name


@type(
    ProductTranslationBulletPoint,
    filters=ProductTranslationBulletPointFilter,
    order=ProductTranslationBulletPointOrder,
    pagination=True,
    fields="__all__",
)
class ProductTranslationBulletPointType(relay.Node, GetQuerysetMultiTenantMixin):
    product_translation: Optional[ProductTranslationType]
