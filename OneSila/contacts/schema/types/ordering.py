from core.schema.types.ordering import order
from core.schema.types.types import auto

from contacts.models import Company


@order(Company)
class CompanyOrder:
    name: auto
