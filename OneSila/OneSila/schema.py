from django.conf import settings

import strawberry
import strawberry_django

from strawberry import auto
from strawberry_django import auth, mutations
from strawberry_django.optimizer import DjangoOptimizerExtension

from contacts.schema import ContactsQuery, ContactsMutation, ContactsSubscription
from core.schema.countries import CountryQuery
from core.schema.languages import LanguageQuery
from core.schema.multi_tenant import MultiTenantQuery, MultiTenantMutation, MultiTenantSubscription
from core.schema.timezones import TimeZoneQuery
from currencies.schema import CurrenciesQuery, CurrenciesMutation, CurrenciesSubscription
from eancodes.schema import EanCodesQuery, EanCodesMutation, EanCodesSubscription
from lead_times.schema import LeadTimesQuery
from media.schema import MediaQuery, MediaMutation, MediaSubscription
from products.schema import ProductsQuery, ProductsMutation, ProductsSubscription
from products_inspector.schema import ProductsInspectorSubscription, ProductsInspectorMutation
from properties.schema import PropertiesQuery, PropertiesMutation, PropertiesSubscription
from sales_prices.schema import SalesPricesQuery, SalesPricesMutation, SalesPriceSubscription
from sales_channels.schema import SalesChannelsQuery, SalesChannelsMutation, SalesChannelsSubscription
from sales_channels.integrations.magento2.schema import MagentoSalesChannelMutation
from taxes.schema import TaxesQuery, TaxesMutation, TaxSubscription
from translations.schema import TranslationsQuery
from integrations.schema import IntegrationsQuery


#
# Actual Query and Mutation declarations
#

@strawberry.type
class Query(CurrenciesQuery, CountryQuery, EanCodesQuery, IntegrationsQuery,
        LanguageQuery, LeadTimesQuery, MediaQuery, MultiTenantQuery,
        ProductsQuery, PropertiesQuery, SalesPricesQuery, SalesChannelsQuery,
        TaxesQuery, TimeZoneQuery, TranslationsQuery):
    pass


@strawberry.type
class Mutation(CurrenciesMutation, EanCodesMutation,MediaMutation, MultiTenantMutation,
       ProductsInspectorMutation, ProductsMutation, PropertiesMutation,
        SalesPricesMutation, SalesChannelsMutation, MagentoSalesChannelMutation, TaxesMutation):
    pass


@strawberry.type
class Subscription(CurrenciesSubscription,EanCodesSubscription, MediaSubscription, MultiTenantSubscription,
        ProductsInspectorSubscription, ProductsSubscription, PropertiesSubscription, SalesPriceSubscription,
        SalesChannelsSubscription, TaxSubscription):
    pass

#
# Schema itself.
#


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=[DjangoOptimizerExtension()]
)
