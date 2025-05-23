from typing import Optional

from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin, ExcluideDemoDataFilterMixin, lazy
from contacts.models import Company, Address, Person, Supplier, \
    InvoiceAddress, ShippingAddress, Customer, InventoryShippingAddress


@filter(Company)
class CompanyFilter(SearchFilterMixin):
    id: auto
    name: auto
    language: auto

    is_supplier: auto
    is_customer: auto
    is_influencer: auto
    is_internal_company: auto


@filter(Supplier)
class SupplierFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    name: auto


@filter(Customer)
class CustomerFilter(SearchFilterMixin, ExcluideDemoDataFilterMixin):
    id: auto
    name: auto


@filter(Person)
class PersonFilter(SearchFilterMixin):
    id: auto
    active: auto
    first_name: auto
    last_name: auto
    email: auto
    company: CompanyFilter | None


@filter(Address)
class AddressFilter(SearchFilterMixin):
    id: auto
    company: CompanyFilter | None
    is_invoice_address: auto
    is_shipping_address: auto


@filter(InvoiceAddress)
class InvoiceAddressFilter(SearchFilterMixin):
    id: auto
    company: CompanyFilter | None


@filter(ShippingAddress)
class ShippingAddressFilter(SearchFilterMixin):
    id: auto
    company: CompanyFilter | None
    leadtimeforshippingaddress: Optional[lazy['LeadTimeForShippingAddressFilter', "lead_times.schema.types.filters"]]


@filter(InventoryShippingAddress)
class InventoryShippingAddressFilter(SearchFilterMixin):
    id: auto
    company: CompanyFilter | None
