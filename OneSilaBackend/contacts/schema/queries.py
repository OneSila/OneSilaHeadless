import strawberry
import strawberry_django
from strawberry.relay import ListConnection
from strawberry_django.permissions import IsAuthenticated
from strawberry_django.relay import ListConnectionWithTotalCount

from core.schema.queries import field, connection
from contacts.models import Company
from django.db.models import QuerySet

from typing import List
from .types.types import CompanyType, SupplierType, CustomerType, \
    InfluencerType, InternalCompanyType, PersonType, AddressType, \
    ShippingAddressType, InvoiceAddressType


@strawberry.type(name="Query")
class ContactsQuery:
    company: CompanyType = field()
    companies: ListConnectionWithTotalCount[CompanyType] = connection()

    supplier: SupplierType = field()
    suppliers: ListConnectionWithTotalCount[SupplierType] = connection()

    customer: CustomerType = field()
    customers: ListConnectionWithTotalCount[CustomerType] = connection()

    influencer: InfluencerType = field()
    influencers: ListConnectionWithTotalCount[InfluencerType] = connection()

    internal_company: InternalCompanyType = field()
    internal_companies: ListConnectionWithTotalCount[InternalCompanyType] = connection()

    person: PersonType = field()
    people: ListConnectionWithTotalCount[PersonType] = connection()

    address: AddressType = field()
    addresses: ListConnectionWithTotalCount[AddressType] = connection()

    shipping_address: ShippingAddressType = field()
    shipping_addresses: ListConnectionWithTotalCount[ShippingAddressType] = connection()

    invoice_address: InvoiceAddressType = field()
    invoice_addresses: ListConnectionWithTotalCount[InvoiceAddressType] = connection()
