from media.models import Media
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
from taxes.schema.types.types import VatRateType
from products.models import Product, BundleProduct, ConfigurableProduct, SimpleProduct, \
    ProductTranslation, ConfigurableVariation, BundleVariation, AliasProduct
from properties.schema.types.types import ProductPropertyType
from properties.models import ProductProperty
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
from decimal import Decimal

from strawberry.relay.utils import to_base64
from contacts.schema.types.types import CompanyType
from core.schema.core.types.types import relay, type, field, Annotated, lazy, strawberry_type
from core.schema.core.mixins import GetQuerysetMultiTenantMixin, GetProductQuerysetMultiTenantMixin

from typing import List, Optional


@strawberry_type
class InspectorCompletionBlockType:
    code: int
    completed: bool


@strawberry_type
class InspectorCompletionType:
    percentage: int
    inspector_status: int
    blocks: List[InspectorCompletionBlockType]


@type(Product, filters=ProductFilter, order=ProductOrder, pagination=True, fields="__all__")
class ProductType(relay.Node, GetProductQuerysetMultiTenantMixin):
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
        media_relation = self.mediaproductthrough_set.filter(media__type=Media.IMAGE, is_main_image=True, sales_channel=None)

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
        from products_inspector.constants import RED, ORANGE, GREEN

        if self.inspector.has_missing_information:
            return RED
        elif self.inspector.has_missing_optional_information:
            return ORANGE
        else:
            return GREEN

    @field()
    def percentage_inspector_status(self, info) -> InspectorCompletionType:
        from products_inspector.constants import RED, ORANGE, GREEN

        percentage, blocks = self.inspector.completion_percentage()

        if self.inspector.has_missing_information:
            inspector_status = RED
        elif self.inspector.has_missing_optional_information:
            inspector_status = ORANGE
        else:
            inspector_status = GREEN

        block_types = [
            InspectorCompletionBlockType(code=b["code"], completed=b["completed"])
            for b in blocks
        ]

        return InspectorCompletionType(
            percentage=percentage,
            inspector_status=inspector_status,
            blocks=block_types,
        )

    @field()
    def has_parents(self, info) -> bool:
        return ConfigurableVariation.objects.filter(variation_id=self.id).exists() or BundleVariation.objects.filter(variation_id=self.id).exists()


@type(ProductTranslation, filters=ProductTranslationFilter, order=ProductTranslationOrder, pagination=True, fields="__all__")
class ProductTranslationType(relay.Node, GetQuerysetMultiTenantMixin):
    sales_channel: Optional[Annotated['SalesChannelType', lazy('sales_channels.schema.types.types')]]


@type(BundleProduct, filters=BundleProductFilter, order=BundleProductOrder, pagination=True, fields="__all__")
class BundleProductType(relay.Node, GetProductQuerysetMultiTenantMixin):
    pass


@type(ConfigurableProduct, filters=ConfigurableProductFilter, order=ConfigurableProductOrder, pagination=True, fields="__all__")
class ConfigurableProductType(relay.Node, GetProductQuerysetMultiTenantMixin):
    pass


@type(SimpleProduct, filters=SimpleProductFilter, order=SimpleProductOrder, pagination=True, fields="__all__")
class SimpleProductType(relay.Node, GetProductQuerysetMultiTenantMixin):
    @field()
    def name(self, info) -> str | None:
        return self.name


@type(ConfigurableVariation, filters=ConfigurableVariationFilter, order=ConfigurableVariationOrder, pagination=True, fields="__all__")
class ConfigurableVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    parent: Optional[ProductType]
    variation: Optional[ProductType]

    @field()
    def configurator_value(self, info) -> str | None:
        return self.configurator_value


@type(BundleVariation, filters=BundleVariationFilter, order=BundleVariationOrder, pagination=True, fields="__all__")
class BundleVariationType(relay.Node, GetQuerysetMultiTenantMixin):
    parent: Optional[ProductType]
    variation: Optional[ProductType]


@type(AliasProduct, filters=AliasProductFilter, order=AliasProductOrder, pagination=True, fields="__all__")
class AliasProductType(relay.Node, GetProductQuerysetMultiTenantMixin):

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


@strawberry_type
class ProductVariationsTaskResponse:
    success: bool
