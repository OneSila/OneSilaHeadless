import strawberry_django
from strawberry import auto

from contacts.models import Company


@strawberry_django.ordering.order(Company)
class CompanyOrder:
    name: auto
