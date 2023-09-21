from core.schema import TypeMultiTenantFilterMixin

import strawberry
import strawberry.django
from strawberry import auto
from asgiref.sync import sync_to_async

from typing import List

from contacts.models import Company, Supplier, Customer, Influencer, \
    InternalCompany, Person, Address, ShippingAddress, InvoiceAddress
from .filters import CompanyFilter, AddressFilter, PersonFilter
from .ordering import CompanyOrder

from strawberry import relay


@strawberry.django.type(Company, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class CompanyType(relay.Node, TypeMultiTenantFilterMixin):
    related_companies: List['CompanyType']


@strawberry.django.type(Supplier, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class SupplierType(relay.Node, TypeMultiTenantFilterMixin):
    related_companies: List['CompanyType']


@strawberry.django.type(Customer, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class CustomerType(relay.Node, TypeMultiTenantFilterMixin):
    related_companies: List['CompanyType']


@strawberry.django.type(Influencer, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class InfluencerType(relay.Node, TypeMultiTenantFilterMixin):
    related_companies: List['CompanyType']


@strawberry.django.type(InternalCompany, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class InternalCompanyType(relay.Node, TypeMultiTenantFilterMixin):
    related_companies: List['CompanyType']


@strawberry.django.type(Person, filters=PersonFilter, pagination=True, fields='__all__')
class PersonType(relay.Node, TypeMultiTenantFilterMixin):
    pass


@strawberry.django.type(Address, filters=AddressFilter, pagination=True, fields='__all__')
class AddressType(relay.Node, TypeMultiTenantFilterMixin):
    pass


@strawberry.django.type(ShippingAddress, filters=AddressFilter, pagination=True, fields='__all__')
class ShippingAddressType(relay.Node, TypeMultiTenantFilterMixin):
    pass


@strawberry.django.type(InvoiceAddress, filters=AddressFilter, pagination=True, fields='__all__')
class InvoiceAddressType(relay.Node, TypeMultiTenantFilterMixin):
    pass
