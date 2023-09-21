import strawberry
import strawberry_django

from typing import List
from strawberry_django import mutations
from strawberry_django.permissions import IsAuthenticated

from .types.types import CompanyType
from .types.input import CompanyInput, CompanyPartialInput


@strawberry.type(name="Mutation")
class ContactsMutation:
    create_company: CompanyType = mutations.create(CompanyInput, extensions=[IsAuthenticated()])
    create_companies: List[CompanyType] = mutations.create(CompanyInput, extensions=[IsAuthenticated()])
    update_company: List[CompanyType] = mutations.update(CompanyPartialInput, extensions=[IsAuthenticated()])
    delete_companies: List[CompanyType] = mutations.delete(extensions=[IsAuthenticated()])
