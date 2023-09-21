from django.contrib.auth import get_user_model

import strawberry
import strawberry_django

from strawberry import auto
from strawberry_django import auth, mutations
from strawberry_django.optimizer import DjangoOptimizerExtension

from contacts.schema import ContactsQuery, ContactsMutation


@strawberry_django.type(get_user_model(), fields="__all__")
class UserType:
    pass


@strawberry_django.input(get_user_model())
class UserInput:
    username: auto
    password: auto


@strawberry.type
class Query(ContactsQuery):
    me: UserType = auth.current_user()


@strawberry.type
class Mutation(ContactsMutation):
    login: UserType = auth.login()
    logout = auth.logout()
    register: UserType = auth.register(UserInput)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        DjangoOptimizerExtension,
    ]
)
