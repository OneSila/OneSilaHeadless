from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter, SearchFilterMixin
from contacts.models import Company, Address, Person, Supplier, \
    InvoiceAddress, ShippingAddress, Customer


@filter(Company)
class CompanyFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto

    is_supplier: auto
    is_customer: auto
    is_influencer: auto
    is_internal_company: auto


@filter(Supplier)
class SupplierFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto


@filter(Customer)
class CustomerFilter(SearchFilterMixin):
    search: str | None
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto


@filter(Person)
class PersonFilter(SearchFilterMixin):
    search: str | None
    first_name: auto
    last_name: auto
    email: auto
    company: CompanyFilter | None


@filter(Address)
class AddressFilter(SearchFilterMixin):
    search: str | None
    company: CompanyFilter | None
    is_invoice_address: auto
    is_shipping_address: auto


@filter(InvoiceAddress)
class InvoiceAddressFilter(SearchFilterMixin):
    search: str | None
    company: CompanyFilter | None


@filter(ShippingAddress)
class ShippingAddressFilter(SearchFilterMixin):
    search: str | None
    company: CompanyFilter | None
