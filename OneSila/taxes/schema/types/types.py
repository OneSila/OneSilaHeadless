from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from taxes.models import Tax
from .filters import TaxFilter
from .ordering import TaxOrder


@type(Tax, filters=TaxFilter, order=TaxOrder, pagination=True, fields="__all__")
class TaxType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
