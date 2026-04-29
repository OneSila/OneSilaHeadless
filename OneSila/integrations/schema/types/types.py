from typing import Annotated, Optional, List

from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin, field, lazy
from integrations.models import (
    Integration,
    PublicIntegrationType,
    PublicIntegrationTypeTranslation,
    PublicIssue,
    PublicIssueCategory,
    PublicIssueImage,
    PublicIssueRequest,
)
from integrations.schema.types.filters import (
    IntegrationFilter,
    PublicIntegrationTypeFilter,
    PublicIssueCategoryFilter,
    PublicIssueFilter,
)
from integrations.schema.types.ordering import IntegrationOrder, PublicIntegrationTypeOrder, PublicIssueOrder
from integrations.constants import INTEGRATIONS_TYPES_MAP, MAGENTO_INTEGRATION, MIRAKL_INTEGRATION
from integrations.helpers import get_public_integration_asset_url
from strawberry_django.fields.types import DjangoImageType
from strawberry.relay.utils import to_base64


@type(Integration, filters=IntegrationFilter, order=IntegrationOrder, pagination=True, fields="__all__")
class IntegrationType(relay.Node, GetQuerysetMultiTenantMixin):

    @field()
    def type(self, info) -> str:
        integration_type = INTEGRATIONS_TYPES_MAP.get(self.__class__, MAGENTO_INTEGRATION)
        if integration_type != MIRAKL_INTEGRATION:
            return integration_type

        instance = self.get_real_instance() if hasattr(self, "get_real_instance") else self
        return getattr(instance, "sub_type", None) or MIRAKL_INTEGRATION

    @field()
    def connected(self, info) -> bool:
        from sales_channels.integrations.magento2.models import MagentoSalesChannel
        from sales_channels.integrations.shopify.models import ShopifySalesChannel
        from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
        from sales_channels.integrations.amazon.models import AmazonSalesChannel
        from sales_channels.integrations.ebay.models import EbaySalesChannel
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.mirakl.models import MiraklSalesChannel
        from sales_channels.models import ManualSalesChannel
        from webhooks.models import WebhookIntegration

        if isinstance(self, MagentoSalesChannel):
            return True
        elif isinstance(self, ShopifySalesChannel):
            return self.access_token is not None
        elif isinstance(self, WoocommerceSalesChannel):
            return bool(self.api_key and self.api_secret)
        elif isinstance(self, AmazonSalesChannel):
            return self.access_token is not None
        elif isinstance(self, SheinSalesChannel):
            return bool(self.secret_key)
        elif isinstance(self, WebhookIntegration):
            return True
        elif isinstance(self, EbaySalesChannel):
            return self.access_token is not None
        elif isinstance(self, MiraklSalesChannel):
            return self.connected
        elif isinstance(self, ManualSalesChannel):
            return True

        raise NotImplementedError(f"Integration type {self.__class__} not implemented")

    @field()
    def proxy_id(self, info) -> str:
        from sales_channels.integrations.magento2.models import MagentoSalesChannel
        from sales_channels.integrations.magento2.schema.types.types import MagentoSalesChannelType
        from sales_channels.integrations.shopify.models import ShopifySalesChannel
        from sales_channels.integrations.shopify.schema.types.types import ShopifySalesChannelType
        from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
        from sales_channels.integrations.woocommerce.schema.types.types import WoocommerceSalesChannelType
        from sales_channels.integrations.amazon.models import AmazonSalesChannel
        from sales_channels.integrations.amazon.schema.types.types import AmazonSalesChannelType
        from webhooks.models import WebhookIntegration
        from webhooks.schema.types.types import WebhookIntegrationType
        from sales_channels.integrations.ebay.models import EbaySalesChannel
        from sales_channels.integrations.ebay.schema.types.types import EbaySalesChannelType
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.shein.schema.types.types import SheinSalesChannelType
        from sales_channels.integrations.mirakl.models import MiraklSalesChannel
        from sales_channels.integrations.mirakl.schema.types.types import MiraklSalesChannelType
        from sales_channels.models import ManualSalesChannel
        from sales_channels.schema.types.types import ManualSalesChannelType


        if isinstance(self, MagentoSalesChannel):
            graphql_type = MagentoSalesChannelType
        elif isinstance(self, ShopifySalesChannel):
            graphql_type = ShopifySalesChannelType
        elif isinstance(self, WoocommerceSalesChannel):
            graphql_type = WoocommerceSalesChannelType
        elif isinstance(self, AmazonSalesChannel):
            graphql_type = AmazonSalesChannelType
        elif isinstance(self, SheinSalesChannel):
            graphql_type = SheinSalesChannelType
        elif isinstance(self, WebhookIntegration):
            graphql_type = WebhookIntegrationType
        elif isinstance(self, EbaySalesChannel):
            graphql_type = EbaySalesChannelType
        elif isinstance(self, MiraklSalesChannel):
            graphql_type = MiraklSalesChannelType
        elif isinstance(self, ManualSalesChannel):
            graphql_type = ManualSalesChannelType
        else:
            raise NotImplementedError(f"Integration type {self.__class__} not implemented")

        return to_base64(graphql_type, self.pk)

    @field()
    def icon_svg_url(self, info) -> Optional[str]:
        return get_public_integration_asset_url(
            integration=self,
            field_name="logo_svg",
        )

    @field()
    def logo_png_url(self, info) -> Optional[str]:
        return get_public_integration_asset_url(
            integration=self,
            field_name="logo_png",
        )


@type(
    PublicIntegrationTypeTranslation,
    fields="__all__",
)
class PublicIntegrationTypeTranslationType(relay.Node):
    public_integration_type: Annotated[
        "PublicIntegrationTypeType",
        lazy("integrations.schema.types.types"),
    ]


@type(
    PublicIntegrationType,
    filters=PublicIntegrationTypeFilter,
    order=PublicIntegrationTypeOrder,
    pagination=True,
    fields="__all__",
)
class PublicIntegrationTypeType(relay.Node):
    based_to: Optional[Annotated[
        "PublicIntegrationTypeType",
        lazy("integrations.schema.types.types"),
    ]]
    translations: List[Annotated[
        "PublicIntegrationTypeTranslationType",
        lazy("integrations.schema.types.types"),
    ]]

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.select_related("based_to").prefetch_related("translations", "based_to__translations").order_by(*queryset.model._meta.ordering)

    @field()
    def name(self, info, language: Optional[str] = None) -> str:
        return PublicIntegrationType.name(self, language=language)

    @field()
    def description(self, info, language: Optional[str] = None) -> str:
        return PublicIntegrationType.description(self, language=language)

    @field()
    def icon_svg_url(self, info) -> Optional[str]:
        return get_public_integration_asset_url(
            integration=self,
            field_name="logo_svg",
        )

    @field()
    def logo_png_url(self, info) -> Optional[str]:
        return get_public_integration_asset_url(
            integration=self,
            field_name="logo_png",
        )

@type(PublicIssueRequest, fields=("issue", "description", "submission_id", "product_sku", "status", "created_at", "updated_at"))
class PublicIssueRequestType(relay.Node, GetQuerysetMultiTenantMixin):
    integration_type: Annotated[
        "PublicIntegrationTypeType",
        lazy("integrations.schema.types.types"),
    ]

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.select_related("integration_type")


@type(
    PublicIssueCategory,
    filters=PublicIssueCategoryFilter,
    pagination=True,
    fields=("name", "code", "created_at", "updated_at"),
)
class PublicIssueCategoryType(relay.Node):
    public_issue: Annotated[
        "PublicIssueType",
        lazy("integrations.schema.types.types"),
    ]

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.select_related("public_issue").order_by("code")


@type(PublicIssueImage,fields=("image", "created_at", "updated_at"))
class PublicIssueImageType(relay.Node):
    public_issue: Annotated[
        "PublicIssueType",
        lazy("integrations.schema.types.types"),
    ]
    image: DjangoImageType

    @field()
    def image_url(self, info) -> Optional[str]:
        return self.image_url


@type(
    PublicIssue,
    filters=PublicIssueFilter,
    order=PublicIssueOrder,
    pagination=True,
    fields=("code", "issue", "cause", "recommended_fix", "request_reference", "created_at", "updated_at"),
)
class PublicIssueType(relay.Node):
    integration_type: Optional[Annotated[
        "PublicIntegrationTypeType",
        lazy("integrations.schema.types.types"),
    ]]
    categories: List[Annotated[
        "PublicIssueCategoryType",
        lazy("integrations.schema.types.types"),
    ]]
    images: List[Annotated[
        "PublicIssueImageType",
        lazy("integrations.schema.types.types"),
    ]]

    @classmethod
    def get_queryset(cls, queryset, info, **kwargs):
        return queryset.select_related("integration_type").prefetch_related("categories", "images")
