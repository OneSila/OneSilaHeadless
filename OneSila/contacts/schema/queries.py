from core.schema.core.queries import node, connection, ListConnectionWithTotalCount, type, field, anonymous_field
from contacts.models import Company

from typing import List

from .types.types import CompanyType, SupplierType, CustomerType, \
    InfluencerType, InternalCompanyType, PersonType, AddressType, \
    ShippingAddressType, InvoiceAddressType, CustomerLanguageType, \
    InventoryShippingAddressType
from ..languages import CUSTOMER_LANGUAGE_CHOICES


def get_customer_languages(info) -> List[CustomerLanguageType]:
    return [CustomerLanguageType(code=code, name=name) for code, name in CUSTOMER_LANGUAGE_CHOICES]


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

    inventory_shipping_address: InventoryShippingAddressType = node()
    inventory_shipping_addresses: ListConnectionWithTotalCount[InventoryShippingAddressType] = connection()

    customer_languages: List[CustomerLanguageType] = anonymous_field(resolver=get_customer_languages)
