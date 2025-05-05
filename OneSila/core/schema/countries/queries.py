from core.schema.core.queries import type, anonymous_field

from typing import List

from core.countries import COUNTRY_CHOICES
from core.schema.countries.types.types import CountryType


def get_countries() -> List[CountryType]:
    return [CountryType(code=code, name=name) for code, name in COUNTRY_CHOICES]


@type(name="Query")
class CountryQuery:
    countries: List[CountryType] = anonymous_field(resolver=get_countries)
