from core.schema.core.mutations import create, update, delete, type, List, field

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


@type(name="Mutation")
class ContactsMutation:
    create_company: CompanyType = create(CompanyInput)
    create_companies: List[CompanyType] = create(CompanyInput)
    update_company: CompanyType = update(CompanyPartialInput)
    delete_company: CompanyType = delete()
    delete_companies: List[CompanyType] = delete()

    create_supplier: SupplierType = create(SupplierInput)
    create_suppliers: List[SupplierType] = create(SupplierInput)
    update_supplier: SupplierType = update(SupplierPartialInput)
    delete_supplier: SupplierType = delete()
    delete_suppliers: List[SupplierType] = delete()

    create_customer: CustomerType = create(CustomerInput)
    create_customers: List[CustomerType] = create(CustomerInput)
    update_customer: CompanyType = update(CustomerPartialInput)
    delete_customer: CustomerType = delete()
    delete_customers: List[CustomerType] = delete()

    create_influencer: InfluencerType = create(InfluencerInput)
    create_influencers: List[InfluencerType] = create(InfluencerInput)
    update_influencer: InfluencerType = create(InfluencerPartialInput)
    delete_influencer: InfluencerType = delete()
    delete_influencers: List[InfluencerType] = delete()

    create_internal_company: InternalCompanyType = create(InternalCompanyInput)
    create_internal_companies: List[InternalCompanyType] = create(InternalCompanyInput)
    update_internal_company: InternalCompanyType = update(InternalCompanyPartialInput)
    delete_internal_company: InternalCompanyType = delete()
    delete_internal_companies: List[InternalCompanyType] = delete()

    create_person: PersonType = create(PersonInput)
    create_people: List[PersonType] = create(PersonInput)
    update_person: PersonType = update(PersonPartialInput)
    delete_person: PersonType = delete()
    delete_people: List[PersonType] = delete()

    create_address: AddressType = create(AddressInput)
    create_addresses: List[AddressType] = create(AddressInput)
    update_address: AddressType = update(AddressPartialInput)
    delete_address: List[AddressType] = delete()
    delete_addresses: AddressType = delete()

    create_shipping_address: ShippingAddressType = create(ShippingAddressInput)
    create_shipping_addresses: List[ShippingAddressType] = create(ShippingAddressInput)
    update_shipping_address: List[ShippingAddressType] = update(ShippingAddressInput)
    delete_shipping_address: List[ShippingAddressType] = delete()
    delete_shipping_addresses: ShippingAddressType = delete()

    create_invoice_address: InvoiceAddressType = create(InvoiceAddressInput)
    create_invoice_addresses: List[InvoiceAddressType] = create(InvoiceAddressInput)
    update_invoice_address: List[InvoiceAddressType] = update(InvoiceAddressInput)
    delete_invoice_address: List[InvoiceAddressType] = delete()
    delete_invoice_addresses: InvoiceAddressType = delete()
