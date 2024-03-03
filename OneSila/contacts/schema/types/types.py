from core.schema.core.types.types import type, relay, List, Annotated, lazy, strawberry_type
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.multi_tenant.types.types import MultiTenantCompanyType

from contacts.models import Company, Supplier, Customer, Influencer, \
    InternalCompany, Person, Address, ShippingAddress, InvoiceAddress
from .filters import CompanyFilter, SupplierFilter, AddressFilter, PersonFilter, CustomerFilter
from .ordering import CompanyOrder, SupplierOrder, CustomerOrder, PersonOrder


@type(Company, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class CompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Supplier, filters=SupplierFilter, order=SupplierOrder, pagination=True, fields="__all__")
class SupplierType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Customer, filters=CustomerFilter, order=CustomerOrder, pagination=True, fields="__all__")
class CustomerType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Influencer, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InfluencerType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(InternalCompany, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InternalCompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    related_companies: List['CompanyType'] | None
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Person, filters=PersonFilter, order=PersonOrder, pagination=True, fields="__all__")
class PersonType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType


@type(Address, filters=AddressFilter, pagination=True, fields="__all__")
class AddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType
    contact: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(ShippingAddress, filters=AddressFilter, pagination=True, fields="__all__")
class ShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType
    contact: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(InvoiceAddress, filters=AddressFilter, pagination=True, fields="__all__")
class InvoiceAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType
    contact: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]

@strawberry_type
class CustomerLanguageType:
    code: str
    name: str