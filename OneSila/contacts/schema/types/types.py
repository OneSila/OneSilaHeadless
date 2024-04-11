from typing import Optional

from core.schema.core.types.types import type, relay, List, Annotated, lazy, strawberry_type, field
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.multi_tenant.types.types import MultiTenantCompanyType

from contacts.models import Company, Supplier, Customer, Influencer, \
    InternalCompany, Person, Address, ShippingAddress, InvoiceAddress, InternalShippingAddress
from .filters import CompanyFilter, SupplierFilter, AddressFilter, PersonFilter, CustomerFilter, \
    ShippingAddressFilter, InvoiceAddressFilter, InternalShippingAddressFilter
from .ordering import CompanyOrder, SupplierOrder, CustomerOrder, PersonOrder


@type(Company, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class CompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Supplier, filters=SupplierFilter, order=SupplierOrder, pagination=True, fields="__all__")
class SupplierType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Customer, filters=CustomerFilter, order=CustomerOrder, pagination=True, fields="__all__")
class CustomerType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Influencer, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InfluencerType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(InternalCompany, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InternalCompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]

    @field()
    def full_address(self, info) -> str:
        return self.full_address

@type(Person, filters=PersonFilter, order=PersonOrder, pagination=True, fields="__all__")
class PersonType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType

    @field()
    def full_name(self, info) -> str:
        return self.full_name()

@type(Address, filters=AddressFilter, pagination=True, fields="__all__")
class AddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType
    person: Optional[PersonType]

    @field()
    def full_address(self, info) -> str:
        return self.full_address

@type(ShippingAddress, filters=ShippingAddressFilter, pagination=True, fields="__all__")
class ShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType
    person: Optional[PersonType]

    @field()
    def full_address(self, info) -> str:
        return self.full_address


@type(InvoiceAddress, filters=InvoiceAddressFilter, pagination=True, fields="__all__")
class InvoiceAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType
    person: Optional[PersonType]

    @field()
    def full_address(self, info) -> str:
        return self.full_address


@type(InternalShippingAddress, filters=InternalShippingAddressFilter, pagination=True, fields="__all__")
class InternalShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    company: CompanyType
    person: Optional[PersonType]

    @field()
    def full_address(self, info) -> str:
        return self.full_address


@strawberry_type
class CustomerLanguageType:
    code: str
    name: str
