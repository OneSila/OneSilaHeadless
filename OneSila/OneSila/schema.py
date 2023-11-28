from django.conf import settings

import strawberry
import strawberry_django

from strawberry import auto
from strawberry_django import auth, mutations
from strawberry_django.optimizer import DjangoOptimizerExtension

from contacts.schema import ContactsQuery, ContactsMutation, ContactsSubscription
from core.schema.countries import CountryQuery
from core.schema.multi_tenant import MultiTenantQuery, MultiTenantMutation, MultiTenantSubscription
from currencies.schema import CurrenciesQuery, CurrenciesMutation, CurrenciesSubscription
from customs.schema import CustomsQuery, CustomsMutation, CustomsSubscription
from eancodes.schema import EanCodesQuery, EanCodesMutation, EanCodesSubscription
from inventory.schema import InventoryQuery, InventoryMutation, InventorySubscription
from media.schema import MediaQuery, MediaMutation, MediaSubscription
from orders.schema import OrdersQuery, OrdersMutation, OrdersSubscription
from products.schema import ProductsQuery, ProductsMutation, ProductsSubscription
from properties.schema import PropertiesQuery, PropertiesMutation, PropertiesSubscription
from purchasing.schema import PurchasingQuery, PurchasingMutation, PurchasingSubscription
from sales_prices.schema import SalesPricesQuery, SalesPricesMutation, SalesPriceSubscription
from taxes.schema import TaxesQuery, TaxesMutation, TaxSubscription
from units.schema import UnitsQuery, UnitsMutation, UnitsSubscription


#
# Actual Query and Mutation declarations
#

@strawberry.type
class Query(ContactsQuery, CurrenciesQuery, CustomsQuery, CountryQuery, EanCodesQuery,
        InventoryQuery, MediaQuery, MultiTenantQuery, OrdersQuery, ProductsQuery,
        PropertiesQuery, PurchasingQuery, SalesPricesQuery, TaxesQuery, UnitsQuery):
    pass


@strawberry.type
class Mutation(ContactsMutation, CurrenciesMutation, CustomsMutation, EanCodesMutation,
        InventoryMutation, MediaMutation, MultiTenantMutation, OrdersMutation,
        ProductsMutation, PropertiesMutation, PurchasingMutation, SalesPricesMutation,
        TaxesMutation, UnitsMutation):
    pass


@strawberry.type
class Subscription(ContactsSubscription, CurrenciesSubscription,
        CustomsSubscription, EanCodesSubscription, InventorySubscription,
        MediaSubscription, MultiTenantSubscription, OrdersSubscription,
        ProductsSubscription, PropertiesSubscription, PurchasingSubscription,
        SalesPriceSubscription, TaxSubscription, UnitsSubscription):
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
