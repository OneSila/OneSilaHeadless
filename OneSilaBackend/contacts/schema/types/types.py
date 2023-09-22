from core.schema.types.types import type, relay
from core.schema.mixins import GetQuerysetMultiTenantMixin

from typing import List

from contacts.models import Company, Supplier, Customer, Influencer, \
    InternalCompany, Person, Address, ShippingAddress, InvoiceAddress
from .filters import CompanyFilter, AddressFilter, PersonFilter
from .ordering import CompanyOrder


@type(Company, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class CompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None


@type(Supplier, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class SupplierType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None


@type(Customer, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class CustomerType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None


@type(Influencer, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InfluencerType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None


@type(InternalCompany, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InternalCompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None


@type(Person, filters=PersonFilter, pagination=True, fields="__all__")
class PersonType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(Address, filters=AddressFilter, pagination=True, fields="__all__")
class AddressType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(ShippingAddress, filters=AddressFilter, pagination=True, fields="__all__")
class ShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    pass


@type(InvoiceAddress, filters=AddressFilter, pagination=True, fields="__all__")
class InvoiceAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
