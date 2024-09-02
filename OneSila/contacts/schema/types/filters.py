from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin
from contacts.models import Company, Address, Person, Supplier, \
    InvoiceAddress, ShippingAddress, Customer, InventoryShippingAddress


@filter(Company)
class CompanyFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    language: auto

    is_supplier: auto
    is_customer: auto
    is_influencer: auto
    is_internal_company: auto


@filter(Supplier)
class SupplierFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    search: str | None
    id: auto
    name: auto
    exclude_demo_data: Optional[bool]


@filter(Customer)
class CustomerFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    search: str | None
    id: auto
    name: auto
    exclude_demo_data: Optional[bool]


@filter(Person)
class PersonFilter(SearchFilterMixin):
    id: auto
    search: str | None
    active: auto
    first_name: auto
    last_name: auto
    email: auto
    company: CompanyFilter | None


@filter(Address)
class AddressFilter(SearchFilterMixin):
    id: auto
    search: str | None
    company: CompanyFilter | None
    is_invoice_address: auto
    is_shipping_address: auto


@filter(InvoiceAddress)
class InvoiceAddressFilter(SearchFilterMixin):
    id: auto
    search: str | None
    company: CompanyFilter | None


@filter(ShippingAddress)
class ShippingAddressFilter(SearchFilterMixin):
    id: auto
    search: str | None
    company: CompanyFilter | None


@filter(InventoryShippingAddress)
class InventoryShippingAddressFilter(SearchFilterMixin):
    id: auto
    search: str | None
    company: CompanyFilter | None
