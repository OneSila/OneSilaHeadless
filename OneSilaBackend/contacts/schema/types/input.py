import strawberry
import strawberry_django
from strawberry import auto


from contacts.models import Company


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


@strawberry_django.input(Company, partial=True)
class CompanyPartialInput:
    name: auto
    vat_number: auto
    eori_number: auto
    related_companies: auto

    is_supplier: auto
    is_customer: auto
    is_influencer: auto
    is_internal_company: auto
