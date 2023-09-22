from django.contrib.auth import get_user_model
from django.conf import settings

import strawberry
import strawberry_django

from strawberry import auto
from strawberry_django import auth, mutations
from strawberry_django.optimizer import DjangoOptimizerExtension

from contacts.schema import ContactsQuery, ContactsMutation
from currencies.schema import CurrencyQuery, CurrencyMutation

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
class Query(ContactsQuery, CurrencyQuery):
    me: UserType = auth.current_user()


@strawberry.type
class Mutation(ContactsMutation, CurrencyMutation):
    login: UserType = auth.login()
    logout = auth.logout()
    register: UserType = auth.register(UserInput)


#
# Schema itself.
#

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[DjangoOptimizerExtension()]
)
