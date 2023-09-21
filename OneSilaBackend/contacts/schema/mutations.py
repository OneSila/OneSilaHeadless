import strawberry
import strawberry_django

from core.schema import CreateMutation, UpdateMutation, \
    DeleteMutation

from typing import List
from strawberry_django import mutations
from strawberry_django.permissions import IsAuthenticated

from .types.types import CompanyType, SupplierType, CustomerType, \
    InfluencerType, InternalCompanyType, PersonType, AddressType, \
    ShippingAddressType, InvoiceAddressType
from .types.input import CompanyInput, CompanyPartialInput, \
    SupplierInput, SupplierPartialInput, CustomerInput, \
    CustomerPartialInput, InfluencerInput, InfluencerPartialInput, \
    InternalCompanyInput, InternalCompanyPartialInput, \
    PersonInput, PersonPartialInput, AddressInput, AddressPartialInput, \
    ShippingAddressInput, ShippingAddressPartialInput, \
    InvoiceAddressInput, InvoiceAddressPartialInput

from strawberry_django import NodeInput


@strawberry.type(name="Mutation")
class ContactsMutation:
    create_company: CompanyType = CreateMutation(CompanyInput, extensions=[IsAuthenticated()])
    create_companies: List[CompanyType] = CreateMutation(CompanyInput, extensions=[IsAuthenticated()])
    update_company: List[CompanyType] = UpdateMutation(CompanyPartialInput, extensions=[IsAuthenticated()])
    delete_company: CompanyType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_companies: List[CompanyType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])

    create_supplier: SupplierType = CreateMutation(SupplierInput, extensions=[IsAuthenticated()])
    create_suppliers: List[SupplierType] = CreateMutation(SupplierInput, extensions=[IsAuthenticated()])
    update_supplier: SupplierType = UpdateMutation(SupplierPartialInput, extensions=[IsAuthenticated()])
    delete_supplier: SupplierType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_suppliers: List[SupplierType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])

    create_customer: CustomerType = CreateMutation(CustomerInput, extensions=[IsAuthenticated()])
    create_customers: List[CustomerType] = CreateMutation(CustomerInput, extensions=[IsAuthenticated()])
    update_customer: CustomerType = UpdateMutation(CustomerPartialInput, extensions=[IsAuthenticated()])
    delete_customer: CustomerType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_customers: List[CustomerType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])

    create_influencer: InfluencerType = CreateMutation(InfluencerInput, extensions=[IsAuthenticated()])
    create_influencers: List[InfluencerType] = CreateMutation(InfluencerInput, extensions=[IsAuthenticated()])
    update_influencer: InfluencerType = CreateMutation(InfluencerPartialInput, extensions=[IsAuthenticated()])
    delete_influencer: InfluencerType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_influencers: List[InfluencerType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])

    create_internal_company: InternalCompanyType = CreateMutation(InternalCompanyInput, extensions=[IsAuthenticated()])
    create_internal_companies: List[InternalCompanyType] = CreateMutation(InternalCompanyInput, extensions=[IsAuthenticated()])
    update_internal_company: InternalCompanyType = UpdateMutation(InternalCompanyPartialInput, extensions=[IsAuthenticated()])
    delete_internal_company: InternalCompanyType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_internal_companies: List[InternalCompanyType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])

    create_person: PersonType = CreateMutation(PersonInput, extensions=[IsAuthenticated()])
    create_people: List[PersonType] = CreateMutation(PersonInput, extensions=[IsAuthenticated()])
    update_person: PersonType = UpdateMutation(PersonPartialInput, extensions=[IsAuthenticated()])
    delete_person: PersonType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_people: List[PersonType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])

    create_address: AddressType = CreateMutation(AddressInput, extensions=[IsAuthenticated()])
    create_addresses: List[AddressType] = CreateMutation(AddressInput, extensions=[IsAuthenticated()])
    update_address: AddressType = UpdateMutation(AddressPartialInput, extensions=[IsAuthenticated()])
    delete_address: List[AddressType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_addresses: AddressType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])

    create_shipping_address: ShippingAddressType = CreateMutation(ShippingAddressInput, extensions=[IsAuthenticated()])
    create_shipping_addresses: List[ShippingAddressType] = CreateMutation(ShippingAddressInput, extensions=[IsAuthenticated()])
    update_shipping_address: List[ShippingAddressType] = UpdateMutation(ShippingAddressInput, extensions=[IsAuthenticated()])
    delete_shipping_address: List[ShippingAddressType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_shipping_addresses: ShippingAddressType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])

    create_invoice_address: InvoiceAddressType = CreateMutation(InvoiceAddressInput, extensions=[IsAuthenticated()])
    create_invoice_addresses: List[InvoiceAddressType] = CreateMutation(InvoiceAddressInput, extensions=[IsAuthenticated()])
    update_invoice_address: List[InvoiceAddressType] = UpdateMutation(InvoiceAddressInput, extensions=[IsAuthenticated()])
    delete_invoice_address: List[InvoiceAddressType] = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
    delete_invoice_addresses: InvoiceAddressType = DeleteMutation(NodeInput, extensions=[IsAuthenticated()])
