from core.schema.core.types.ordering import order
from core.schema.core.types.types import auto

from contacts.models import Company, Supplier, Customer, Person


@order(Company)
class CompanyOrder:
    name: auto


@order(Person)
class PersonOrder:
    first_name: auto
    last_name: auto


@order(Supplier)
class SupplierOrder:
    name: auto


@order(Customer)
class CustomerOrder:
    name: auto
