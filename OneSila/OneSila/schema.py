from django.conf import settings

import strawberry
import strawberry_django

from strawberry import auto
from strawberry_django import auth, mutations
from strawberry_django.optimizer import DjangoOptimizerExtension

from core.schema.countries import CountryQuery
from core.schema.languages import LanguageQuery
from core.schema.multi_tenant import MultiTenantQuery, MultiTenantMutation, MultiTenantSubscription
from core.schema.timezones import TimeZoneQuery
from currencies.schema import CurrenciesQuery, CurrenciesMutation, CurrenciesSubscription
from eancodes.schema import EanCodesQuery, EanCodesMutation, EanCodesSubscription
from media.schema import MediaQuery, MediaMutation, MediaSubscription
from notifications.schema import NotificationsQuery, NotificationsMutation
from products.schema import ProductsQuery, ProductsMutation, ProductsSubscription
from workflows.schema import WorkflowsMutation, WorkflowsQuery, WorkflowsSubscription
from products_inspector.schema import ProductsInspectorSubscription, ProductsInspectorMutation
from properties.schema import PropertiesQuery, PropertiesMutation, PropertiesSubscription
from sales_channels.integrations.ebay.schema import EbaySalesChannelMutation, EbaySalesChannelsQuery, \
        EbaySalesChannelsSubscription
from sales_prices.schema import SalesPricesQuery, SalesPricesMutation, SalesPriceSubscription
from sales_channels.schema import SalesChannelsQuery, SalesChannelsMutation, SalesChannelsSubscription
from sales_channels.integrations.magento2.schema import MagentoSalesChannelMutation, MagentoSalesChannelsQuery, \
    MagentoSalesChannelsSubscription
from sales_channels.integrations.shopify.schema import ShopifySalesChannelMutation, ShopifySalesChannelsQuery, \
    ShopifySalesChannelsSubscription
from sales_channels.integrations.shein.schema import SheinSalesChannelMutation, SheinSalesChannelsQuery, \
    SheinSalesChannelsSubscription
from sales_channels.integrations.mirakl.schema import MiraklSalesChannelMutation, MiraklSalesChannelsQuery, \
    MiraklSalesChannelsSubscription
from sales_channels.integrations.woocommerce.schema import WoocommerceSalesChannelMutation, WoocommerceSalesChannelsQuery, \
    WoocommerceSalesChannelsSubscription
from sales_channels.integrations.amazon.schema import AmazonSalesChannelMutation, AmazonSalesChannelsQuery, \
    AmazonSalesChannelsSubscription
from taxes.schema import TaxesQuery, TaxesMutation, TaxSubscription
from translations.schema import TranslationsQuery
from integrations.schema import IntegrationsQuery, IntegrationsMutation
from imports_exports.schema import ImportsExportsMutation, ImportsExportsQuery, ImportsExportsSubscription
from llm.schema import LlmMutation, LlmQuery
from webhooks.schema import WebhooksQuery, WebhooksMutation


#
# Actual Query and Mutation declarations
#

@strawberry.type
class Query(
        AmazonSalesChannelsQuery,
        CurrenciesQuery,
        CountryQuery,
        EanCodesQuery,
        IntegrationsQuery,
        ImportsExportsQuery,
        LanguageQuery,
        MediaQuery,
        NotificationsQuery,
        MultiTenantQuery,
        MagentoSalesChannelsQuery,
        ShopifySalesChannelsQuery,
        SheinSalesChannelsQuery,
        MiraklSalesChannelsQuery,
        WoocommerceSalesChannelsQuery,
        EbaySalesChannelsQuery,
        ProductsQuery,
        WorkflowsQuery,
        PropertiesQuery,
        SalesPricesQuery,
        SalesChannelsQuery,
        TaxesQuery,
        TimeZoneQuery,
        TranslationsQuery,
        LlmQuery,
        WebhooksQuery,
):
    pass


@strawberry.type
class Mutation(
        AmazonSalesChannelMutation,
        CurrenciesMutation,
        EanCodesMutation,
        MediaMutation,
        NotificationsMutation,
        MultiTenantMutation,
        ShopifySalesChannelMutation,
        SheinSalesChannelMutation,
        MiraklSalesChannelMutation,
        WoocommerceSalesChannelMutation,
        EbaySalesChannelMutation,
        ProductsInspectorMutation,
        ProductsMutation,
        WorkflowsMutation,
        PropertiesMutation,
        IntegrationsMutation,
        ImportsExportsMutation,
        LlmMutation,
        SalesPricesMutation,
        SalesChannelsMutation,
        MagentoSalesChannelMutation,
        TaxesMutation,
        WebhooksMutation,
):
    pass


@strawberry.type
class Subscription(
        AmazonSalesChannelsSubscription,
        CurrenciesSubscription,
        EanCodesSubscription,
        MediaSubscription,
        MultiTenantSubscription,
        ProductsInspectorSubscription,
        ProductsSubscription,
        WorkflowsSubscription,
        PropertiesSubscription,
        SalesPriceSubscription,
        MagentoSalesChannelsSubscription,
        SalesChannelsSubscription,
        TaxSubscription,
        ShopifySalesChannelsSubscription,
        SheinSalesChannelsSubscription,
        MiraklSalesChannelsSubscription,
        WoocommerceSalesChannelsSubscription,
        EbaySalesChannelsSubscription,
        ImportsExportsSubscription,
):
    pass

#
# Schema itself.
#


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[DjangoOptimizerExtension]
)
