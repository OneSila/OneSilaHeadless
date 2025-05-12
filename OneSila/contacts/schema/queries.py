from core.schema.core.queries import node, connection, DjangoListConnection, type, field, anonymous_field
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
    companies: DjangoListConnection[CompanyType] = connection()

    supplier: SupplierType = node()
    suppliers: DjangoListConnection[SupplierType] = connection()

    customer: CustomerType = node()
    customers: DjangoListConnection[CustomerType] = connection()

    influencer: InfluencerType = node()
    influencers: DjangoListConnection[InfluencerType] = connection()

    internal_company: InternalCompanyType = node()
    internal_companies: DjangoListConnection[InternalCompanyType] = connection()

    person: PersonType = node()
    people: DjangoListConnection[PersonType] = connection()

    address: AddressType = node()
    addresses: DjangoListConnection[AddressType] = connection()

    shipping_address: ShippingAddressType = node()
    shipping_addresses: DjangoListConnection[ShippingAddressType] = connection()

    invoice_address: InvoiceAddressType = node()
    invoice_addresses: DjangoListConnection[InvoiceAddressType] = connection()

    inventory_shipping_address: InventoryShippingAddressType = node()
    inventory_shipping_addresses: DjangoListConnection[InventoryShippingAddressType] = connection()

    customer_languages: List[CustomerLanguageType] = anonymous_field(resolver=get_customer_languages)
