import strawberry
import strawberry_django
from strawberry import auto
from strawberry.relay import Node
from strawberry_django import NodeInput

from contacts.models import Company, Supplier, Customer, \
    Influencer, InternalCompany, Person, Address, \
    ShippingAddress, InvoiceAddress


@strawberry_django.input(Company)
class CompanyInput:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto

    is_supplier: auto
    is_customer: auto
    is_influencer: auto
    is_internal_company: auto


@strawberry_django.partial(Company)
class CompanyPartialInput(NodeInput):
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto

    is_supplier: auto
    is_customer: auto
    is_influencer: auto
    is_internal_company: auto


@strawberry_django.input(Supplier)
class SupplierInput:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto


@strawberry_django.input(Supplier)
class SupplierPartialInput:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto


@strawberry_django.input(Customer)
class CustomerInput:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto


@strawberry_django.input(Customer)
class CustomerPartialInput:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto


@strawberry_django.input(Influencer)
class InfluencerInput:
    id: auto
    name: auto
    vat_number: auto
    related_companies: auto


@strawberry_django.input(Influencer)
class InfluencerPartialInput:
    id: auto
    name: auto
    vat_number: auto
    related_companies: auto


@strawberry_django.input(InternalCompany)
class InternalCompanyInput:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto


@strawberry_django.input(InternalCompany)
class InternalCompanyPartialInput:
    id: auto
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto


@strawberry_django.input(Person)
class PersonInput:
    id: auto
    first_name: auto
    last_name: auto
    company: auto
    phone: auto
    email: auto
    language: auto


@strawberry_django.input(Person)
class PersonPartialInput:
    id: auto
    first_name: auto
    last_name: auto
    company: auto
    phone: auto
    email: auto
    language: auto


@strawberry_django.input(Address)
class AddressInput:
    id: auto
    contact: auto
    company: auto
    address1: auto
    address2: auto
    address3: auto
    postcode: auto
    city: auto
    country: auto
    is_invoice_address: auto
    is_shipping_address: auto


@strawberry_django.input(Address)
class AddressPartialInput:
    id: auto
    contact: auto
    company: auto
    address1: auto
    address2: auto
    address3: auto
    postcode: auto
    city: auto
    country: auto
    is_invoice_address: auto
    is_shipping_address: auto


@strawberry_django.input(ShippingAddress)
class ShippingAddressInput:
    id: auto
    contact: auto
    company: auto
    address1: auto
    address2: auto
    address3: auto
    postcode: auto
    city: auto
    country: auto


@strawberry_django.input(ShippingAddress)
class ShippingAddressPartialInput:
    id: auto
    contact: auto
    company: auto
    address1: auto
    address2: auto
    address3: auto
    postcode: auto
    city: auto
    country: auto


@strawberry_django.input(InvoiceAddress)
class InvoiceAddressInput:
    id: auto
    contact: auto
    company: auto
    address1: auto
    address2: auto
    address3: auto
    postcode: auto
    city: auto
    country: auto


@strawberry_django.input(InvoiceAddress)
class InvoiceAddressPartialInput:
    id: auto
    contact: auto
    company: auto
    address1: auto
    address2: auto
    address3: auto
    postcode: auto
    city: auto
    country: auto
