from core.schema.types.types import auto
from core.schema.types.input import NodeInput, input, partial

from contacts.models import Company, Supplier, Customer, \
    Influencer, InternalCompany, Person, Address, \
    ShippingAddress, InvoiceAddress


@input(Company, fields="__all__")
class CompanyInput:
    pass


@partial(Company, fields="__all__")
class CompanyPartialInput(NodeInput):
    pass


@input(Supplier, fields="__all__")
class SupplierInput:
    pass


@partial(Supplier, fields="__all__")
class SupplierPartialInput:
    pass


@input(Customer, fields="__all__")
class CustomerInput:
    pass


@partial(Customer, fields="__all__")
class CustomerPartialInput:
    pass


@input(Influencer, fields="__all__")
class InfluencerInput:
    pass


@partial(Influencer, fields="__all__")
class InfluencerPartialInput:
    pass


@input(InternalCompany, fields="__all__")
class InternalCompanyInput:
    pass


@partial(InternalCompany, fields="__all__")
class InternalCompanyPartialInput:
    pass


@input(Person, fields="__all__")
class PersonInput:
    pass


@partial(Person, fields="__all__")
class PersonPartialInput:
    pass


@input(Address, fields="__all__")
class AddressInput:
    pass


@partial(Address, fields="__all__")
class AddressPartialInput:
    pass


@input(ShippingAddress, fields="__all__")
class ShippingAddressInput:
    pass


@partial(ShippingAddress, fields="__all__")
class ShippingAddressPartialInput:
    pass


@input(InvoiceAddress, fields="__all__")
class InvoiceAddressInput:
    pass


@partial(InvoiceAddress, fields="__all__")
class InvoiceAddressPartialInput:
    pass
