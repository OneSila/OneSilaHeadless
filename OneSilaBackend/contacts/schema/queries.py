import strawberry
import strawberry_django
from strawberry.relay import ListConnection
from strawberry_django.permissions import IsAuthenticated
from strawberry_django.relay import ListConnectionWithTotalCount

from contacts.models import Company
from django.db.models import QuerySet

from typing import List
from .types.types import CompanyType, SupplierType, CustomerType, \
    InfluencerType, InternalCompanyType, PersonType, AddressType, \
    ShippingAddressType, InvoiceAddressType


@strawberry.type(name="Query")
class ContactsQuery:
    company: CompanyType = strawberry_django.field(extensions=[IsAuthenticated()])
    companies: ListConnectionWithTotalCount[CompanyType] = strawberry_django.connection(extensions=[IsAuthenticated()])

    supplier: SupplierType = strawberry_django.field(extensions=[IsAuthenticated()])
    suppliers: ListConnectionWithTotalCount[SupplierType] = strawberry_django.connection(extensions=[IsAuthenticated()])

    customer: CustomerType = strawberry_django.field(extensions=[IsAuthenticated()])
    customers: ListConnectionWithTotalCount[CustomerType] = strawberry_django.connection(extensions=[IsAuthenticated()])

    influencer: InfluencerType = strawberry_django.field(extensions=[IsAuthenticated()])
    influencers: ListConnectionWithTotalCount[InfluencerType] = strawberry_django.connection(extensions=[IsAuthenticated()])

    internal_company: InternalCompanyType = strawberry_django.field(extensions=[IsAuthenticated()])
    internal_companies: ListConnectionWithTotalCount[InternalCompanyType] = strawberry_django.connection(extensions=[IsAuthenticated()])

    person: PersonType = strawberry_django.field(extensions=[IsAuthenticated()])
    people: ListConnectionWithTotalCount[PersonType] = strawberry_django.connection(extensions=[IsAuthenticated()])

    address: AddressType = strawberry_django.field(extensions=[IsAuthenticated()])
    addresses: ListConnectionWithTotalCount[AddressType] = strawberry_django.connection(extensions=[IsAuthenticated()])

    shipping_address: ShippingAddressType = strawberry_django.field(extensions=[IsAuthenticated()])
    shipping_addresses: ListConnectionWithTotalCount[ShippingAddressType] = strawberry_django.connection(extensions=[IsAuthenticated()])

    invoice_address: InvoiceAddressType = strawberry_django.field(extensions=[IsAuthenticated()])
    invoice_addresses: ListConnectionWithTotalCount[InvoiceAddressType] = strawberry_django.connection(extensions=[IsAuthenticated()])
