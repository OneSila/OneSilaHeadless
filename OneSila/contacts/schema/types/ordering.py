from core.schema.types.ordering import order
from core.schema.types.types import auto

from contacts.models import Company, Supplier


@order(Company)
class CompanyOrder:
    name: auto


@order(Supplier)
class SupplierOrder:
    name: auto
