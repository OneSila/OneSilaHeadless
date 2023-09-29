from django.contrib.auth import get_user_model
from django.conf import settings

import strawberry
import strawberry_django

from strawberry import auto
from strawberry_django import auth, mutations
from strawberry_django.optimizer import DjangoOptimizerExtension

from contacts.schema import ContactsQuery, ContactsMutation, ContactsSubscription
from currencies.schema import CurrenciesQuery, CurrenciesMutation
from eancodes.schema import EanCodesQuery, EanCodesMutation
from inventory.schema import InventoryQuery, InventoryMutation
from media.schema import MediaQuery, MediaMutation
from orders.schema import OrdersQuery, OrdersMutation
from products.schema import ProductsQuery, ProductsMutation
from properties.schema import PropertiesQuery, PropertiesMutation
from purchasing.schema import PurchasingQuery, PurchasingMutation
from sales_prices.schema import SalesPricesQuery, SalesPricesMutation
from taxes.schema import TaxesQuery, TaxesMutation
from units.schema import UnitsQuery, UnitsMutation

#
# user types, used to user information in the main schema
#


@strawberry_django.type(get_user_model(), fields="__all__")
class UserType:
    pass


@strawberry_django.input(get_user_model())
class UserInput:
    username: auto
    password: auto


#
# Actual Query and Mutation declarations
#

@strawberry.type
class Query(ContactsQuery, CurrenciesQuery, EanCodesQuery, InventoryQuery,
        MediaQuery, OrdersQuery, ProductsQuery, PropertiesQuery, PurchasingQuery,
        SalesPricesQuery, TaxesQuery, UnitsQuery):
    me: UserType = auth.current_user()


@strawberry.type
class Mutation(ContactsMutation, CurrenciesMutation, EanCodesMutation,
        InventoryMutation, MediaMutation, OrdersMutation, ProductsMutation,
        PropertiesMutation, PurchasingMutation, SalesPricesMutation,
        TaxesMutation, UnitsMutation
               ):
    login: UserType = auth.login()
    logout = auth.logout()
    register: UserType = auth.register(UserInput)


@strawberry.type
class Subscription(ContactsSubscription):
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
