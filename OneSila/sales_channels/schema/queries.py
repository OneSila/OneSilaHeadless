from core.schema.core.queries import node, connection, DjangoListConnection, type, field
from strawberry.relay import from_base64, to_base64

from core.schema.core.helpers import get_multi_tenant_company
from integrations.schema.types.types import IntegrationType
from properties.models import PropertySelectValue
from sales_channels.integrations.amazon.models.properties import AmazonPropertySelectValue
from sales_channels.integrations.ebay.models.properties import EbayPropertySelectValue
from sales_channels.integrations.magento2.models.properties import MagentoPropertySelectValue
from sales_channels.integrations.shein.models.properties import SheinPropertySelectValue
from sales_channels.integrations.woocommerce.models import WoocommerceGlobalAttributeValue
from .types.types import (
    RemoteLogType,
    RemoteProductType,
    SalesChannelType,
    SalesChannelIntegrationPricelistType,
    SalesChannelViewType,
    SalesChannelViewAssignType,
    SalesChannelContentTemplateType,
    RemoteLanguageType,
    RemoteCurrencyType,
    SalesChannelImportType,
    RemotePropertySelectValueMirrorType,
    RemotePropertyType,
    RemotePropertySelectValueType,
)
from .types.types import RemoteLogType, RemoteProductType, SalesChannelType, \
    SalesChannelIntegrationPricelistType, SalesChannelViewType, SalesChannelViewAssignType, RemoteLanguageType, \
    RemoteCurrencyType, SalesChannelImportType, IntegrationType


@type(name='Query')
class SalesChannelsQuery:
    sales_channel_import: SalesChannelImportType = node()
    sales_channel_imports: DjangoListConnection[SalesChannelImportType] = connection()

    remote_log: RemoteLogType = node()
    remote_logs: DjangoListConnection[RemoteLogType] = connection()

    remote_product: RemoteProductType = node()
    remote_products: DjangoListConnection[RemoteProductType] = connection()

    sales_channel: SalesChannelType = node()
    sales_channels: DjangoListConnection[SalesChannelType] = connection()

    sales_channel_integration_pricelist: SalesChannelIntegrationPricelistType = node()
    sales_channel_integration_pricelists: DjangoListConnection[SalesChannelIntegrationPricelistType] = connection()

    sales_channel_view: SalesChannelViewType = node()
    sales_channel_views: DjangoListConnection[SalesChannelViewType] = connection()

    remote_language: RemoteLanguageType = node()
    remote_languages: DjangoListConnection[RemoteLanguageType] = connection()

    remote_currency: RemoteCurrencyType = node()
    remote_currencies: DjangoListConnection[RemoteCurrencyType] = connection()

    sales_channel_view_assign: SalesChannelViewAssignType = node()
    sales_channel_view_assigns: DjangoListConnection[SalesChannelViewAssignType] = connection()

    sales_channel_content_template: SalesChannelContentTemplateType = node()
    sales_channel_content_templates: DjangoListConnection[SalesChannelContentTemplateType] = connection()

    remote_property: RemotePropertyType = node()
    remote_properties: DjangoListConnection[RemotePropertyType] = connection()

    integration: IntegrationType = node()

    @field()
    def remote_property_select_value_mirrors(
        self,
        *,
        info,
        property_select_value: str,
    ) -> list[RemotePropertySelectValueMirrorType]:
        from sales_channels.integrations.amazon.schema.types.types import AmazonPropertySelectValueType
        from sales_channels.integrations.ebay.schema.types.types import EbayPropertySelectValueType
        from sales_channels.integrations.shein.schema.types.types import SheinPropertySelectValueType

        def resolve_local_value(*, instance) -> str:
            local_instance = getattr(instance, "local_instance", None)
            if local_instance:
                return local_instance.value
            return "Unknown"

        _, select_value_id = from_base64(property_select_value)
        multi_tenant_company = get_multi_tenant_company(info)
        local_value = PropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
            pk=select_value_id,
        ).first()
        if not local_value:
            return []

        results: list[RemotePropertySelectValueMirrorType] = []

        for instance in WoocommerceGlobalAttributeValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
            local_instance=local_value,
        ).select_related("remote_property", "local_instance"):
            value = resolve_local_value(instance=instance)
            results.append(
                RemotePropertySelectValueMirrorType(
                    value=value,
                    translated_value=value,
                    marketplace=None,
                    proxy_id=to_base64(RemotePropertySelectValueType, instance.pk),
                    remote_property=instance.remote_property,
                )
            )

        for instance in MagentoPropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
            local_instance=local_value,
        ).select_related("remote_property", "local_instance"):
            value = resolve_local_value(instance=instance)
            results.append(
                RemotePropertySelectValueMirrorType(
                    value=value,
                    translated_value=value,
                    marketplace=None,
                    proxy_id=to_base64(RemotePropertySelectValueType, instance.pk),
                    remote_property=instance.remote_property,
                )
            )

        for instance in SheinPropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
            local_instance=local_value,
        ).select_related("remote_property", "local_instance"):
            results.append(
                RemotePropertySelectValueMirrorType(
                    value=instance.value,
                    translated_value=instance.value_en,
                    marketplace=None,
                    proxy_id=to_base64(SheinPropertySelectValueType, instance.pk),
                    remote_property=instance.remote_property,
                )
            )

        for instance in AmazonPropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
            local_instance=local_value,
        ).select_related("amazon_property", "marketplace", "local_instance"):
            results.append(
                RemotePropertySelectValueMirrorType(
                    value=instance.remote_name,
                    translated_value=instance.translated_remote_name,
                    marketplace=instance.marketplace,
                    proxy_id=to_base64(AmazonPropertySelectValueType, instance.pk),
                    remote_property=instance.amazon_property,
                )
            )

        for instance in EbayPropertySelectValue.objects.filter(
            multi_tenant_company=multi_tenant_company,
            local_instance=local_value,
        ).select_related("ebay_property", "marketplace", "local_instance"):
            results.append(
                RemotePropertySelectValueMirrorType(
                    value=instance.localized_value,
                    translated_value=instance.translated_value,
                    marketplace=instance.marketplace,
                    proxy_id=to_base64(EbayPropertySelectValueType, instance.pk),
                    remote_property=instance.ebay_property,
                )
            )

        return results
