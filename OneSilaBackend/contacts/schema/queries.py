from core.schema.queries import node, connection, ListConnectionWithTotalCount, type, field
from contacts.models import Company

from typing import List

from .types.types import CompanyType, SupplierType, CustomerType, \
    InfluencerType, InternalCompanyType, PersonType, AddressType, \
    ShippingAddressType, InvoiceAddressType


@type(name="Query")
class ContactsQuery:
    company: CompanyType = node()
    companies: ListConnectionWithTotalCount[CompanyType] = connection()

    supplier: SupplierType = node()
    suppliers: ListConnectionWithTotalCount[SupplierType] = connection()

    customer: CustomerType = node()
    customers: ListConnectionWithTotalCount[CustomerType] = connection()

    influencer: InfluencerType = node()
    influencers: ListConnectionWithTotalCount[InfluencerType] = connection()

    internal_company: InternalCompanyType = node()
    internal_companies: ListConnectionWithTotalCount[InternalCompanyType] = connection()

    person: PersonType = node()
    people: ListConnectionWithTotalCount[PersonType] = connection()

    address: AddressType = node()
    addresses: ListConnectionWithTotalCount[AddressType] = connection()

    shipping_address: ShippingAddressType = node()
    shipping_addresses: ListConnectionWithTotalCount[ShippingAddressType] = connection()

    invoice_address: InvoiceAddressType = node()
    invoice_addresses: ListConnectionWithTotalCount[InvoiceAddressType] = connection()
