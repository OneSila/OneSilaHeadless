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
from customs.schema import CustomsQuery, CustomsMutation, CustomsSubscription
from eancodes.schema import EanCodesQuery, EanCodesMutation, EanCodesSubscription
from inventory.schema import InventoryQuery, InventoryMutation, InventorySubscription
from lead_times.schema import LeadTimesQuery, LeadTimesMutation, LeadTimesSubscription
from media.schema import MediaQuery, MediaMutation, MediaSubscription
from orders.schema import OrdersQuery, OrdersMutation, OrdersSubscription
from products.schema import ProductsQuery, ProductsMutation, ProductsSubscription
from products_inspector.schema import ProductsInspectorSubscription, ProductsInspectorMutation
from properties.schema import PropertiesQuery, PropertiesMutation, PropertiesSubscription
from sales_prices.schema import SalesPricesQuery, SalesPricesMutation, SalesPriceSubscription
from sales_channels.schema import SalesChannelsQuery, SalesChannelsMutation, SalesChannelsSubscription
from taxes.schema import TaxesQuery, TaxesMutation, TaxSubscription
from units.schema import UnitsQuery, UnitsMutation, UnitsSubscription
from translations.schema import TranslationsQuery


#
# Actual Query and Mutation declarations
#

@strawberry.type
class Query(ContactsQuery, CurrenciesQuery, CustomsQuery, CountryQuery, EanCodesQuery,
        InventoryQuery, LanguageQuery, LeadTimesQuery, MediaQuery, MultiTenantQuery, OrdersQuery,
        ProductsQuery, PropertiesQuery, SalesPricesQuery, SalesChannelsQuery,
        TaxesQuery, TimeZoneQuery, UnitsQuery, TranslationsQuery):
    pass


@strawberry.type
class Mutation(ContactsMutation, CurrenciesMutation, CustomsMutation, EanCodesMutation,
        InventoryMutation, LeadTimesMutation, MediaMutation, MultiTenantMutation,
        OrdersMutation, ProductsInspectorMutation, ProductsMutation, PropertiesMutation,
        SalesPricesMutation, SalesChannelsMutation, TaxesMutation, UnitsMutation):
    pass


@strawberry.type
class Subscription(ContactsSubscription, CurrenciesSubscription,
        CustomsSubscription, EanCodesSubscription, InventorySubscription,
        LeadTimesSubscription, MediaSubscription, MultiTenantSubscription,
        OrdersSubscription, ProductsInspectorSubscription,
        ProductsSubscription, PropertiesSubscription, SalesPriceSubscription, SalesChannelsSubscription,
        TaxSubscription, UnitsSubscription):
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
