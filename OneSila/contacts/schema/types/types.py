from typing import Optional

from core.schema.core.types.types import type, relay, List, Annotated, lazy, strawberry_type, field
from core.schema.core.mixins import GetQuerysetMultiTenantMixin
from core.schema.multi_tenant.types.types import MultiTenantCompanyType

from contacts.models import Company, Supplier, Customer, Influencer, \
    InternalCompany, Person, Address, ShippingAddress, InvoiceAddress, InventoryShippingAddress
from currencies.schema.types.types import CurrencyType
from currencies.models import Currency
from .filters import CompanyFilter, SupplierFilter, AddressFilter, PersonFilter, CustomerFilter, \
    ShippingAddressFilter, InvoiceAddressFilter, InventoryShippingAddressFilter
from .ordering import CompanyOrder, SupplierOrder, CustomerOrder, PersonOrder


@type(Company, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields='__all__')
class CompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    currency: Optional[CurrencyType]
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]

    @field()
    def country(self, info) -> str | None:
        try:
            return InvoiceAddress.objects.filter_multi_tenant(self.multi_tenant_company).filter(company=self).first().get_country_display()
        except Exception:
            return None

    @field()
    def currency_symbol(self, info) -> str | None:
        if self.currency is not None:
            return self.currency.symbol

        return Currency.objects.filter_multi_tenant(self.multi_tenant_company).filter(is_default_currency=True).first().symbol


@type(Supplier, filters=SupplierFilter, order=SupplierOrder, pagination=True, fields="__all__")
class SupplierType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    currency: Optional[CurrencyType]
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Customer, filters=CustomerFilter, order=CustomerOrder, pagination=True, fields="__all__")
class CustomerType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    currency: Optional[CurrencyType]
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(Influencer, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InfluencerType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    currency: Optional[CurrencyType]
    person_set: List[Annotated['PersonType', lazy("contacts.schema.types.types")]]


@type(InternalCompany, filters=CompanyFilter, order=CompanyOrder, pagination=True, fields="__all__")
class InternalCompanyType(relay.Node, GetQuerysetMultiTenantMixin):
    multi_tenant_company: MultiTenantCompanyType | None
    currency: Optional[CurrencyType]
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


@type(InventoryShippingAddress, filters=InventoryShippingAddressFilter, pagination=True, fields="__all__")
class InventoryShippingAddressType(relay.Node, GetQuerysetMultiTenantMixin):
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
