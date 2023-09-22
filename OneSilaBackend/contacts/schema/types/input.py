import strawberry
import strawberry_django
from strawberry import auto
from strawberry.relay import Node
from strawberry_django import NodeInput

from contacts.models import Company, Supplier, Customer, \
    Influencer, InternalCompany, Person, Address, \
    ShippingAddress, InvoiceAddress


@strawberry_django.input(Company, fields="__all__")
class CompanyInput:
    pass


@strawberry_django.partial(Company, fields="__all__")
class CompanyPartialInput(NodeInput):
    pass


@strawberry_django.input(Supplier, fields="__all__")
class SupplierInput:
    pass


@strawberry_django.input(Supplier, fields="__all__")
class SupplierPartialInput:
    pass


@strawberry_django.input(Customer, fields="__all__")
class CustomerInput:
    pass


@strawberry_django.input(Customer, fields="__all__")
class CustomerPartialInput:
    pass


@strawberry_django.input(Influencer, fields="__all__")
class InfluencerInput:
    pass


@strawberry_django.input(Influencer, fields="__all__")
class InfluencerPartialInput:
    pass


@strawberry_django.input(InternalCompany, fields="__all__")
class InternalCompanyInput:
    pass


@strawberry_django.input(InternalCompany, fields="__all__")
class InternalCompanyPartialInput:
    pass


@strawberry_django.input(Person, fields="__all__")
class PersonInput:
    pass


@strawberry_django.input(Person, fields="__all__")
class PersonPartialInput:
    pass


@strawberry_django.input(Address, fields="__all__")
class AddressInput:
    pass


@strawberry_django.input(Address, fields="__all__")
class AddressPartialInput:
    pass


@strawberry_django.input(ShippingAddress, fields="__all__")
class ShippingAddressInput:
    pass


@strawberry_django.input(ShippingAddress, fields="__all__")
class ShippingAddressPartialInput:
    pass


@strawberry_django.input(InvoiceAddress, fields="__all__")
class InvoiceAddressInput:
    pass


@strawberry_django.input(InvoiceAddress, fields="__all__")
class InvoiceAddressPartialInput:
    pass
