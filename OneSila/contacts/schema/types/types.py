from core.schema.core.types.types import type, relay, List
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.multi_tenant.types.types import MultiTenantCompanyType

from contacts.models import Company, Supplier, Customer, Influencer, \
    InternalCompany, Person, Address, ShippingAddress, InvoiceAddress
from .filters import CompanyFilter, SupplierFilter, AddressFilter, PersonFilter, CustomerFilter
from .ordering import CompanyOrder, SupplierOrder, CustomerOrder


@type(Company, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class CompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None


@type(Supplier, filters=SupplierFilter, order=SupplierOrder, pagination=True, fields="__all__")
class SupplierType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None


@type(Customer, filters=CustomerFilter, order=CustomerOrder, pagination=True, fields="__all__")
class CustomerType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None


@type(Influencer, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InfluencerType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None


@type(InternalCompany, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InternalCompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None


@type(Person, filters=PersonFilter, pagination=True, fields="__all__")
class PersonType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None


@type(Address, filters=AddressFilter, pagination=True, fields="__all__")
class AddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None


@type(ShippingAddress, filters=AddressFilter, pagination=True, fields="__all__")
class ShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None


@type(InvoiceAddress, filters=AddressFilter, pagination=True, fields="__all__")
class InvoiceAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
