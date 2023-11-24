from core.schema.core.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from eancodes.models import EanCode
from .filters import EanCodeFilter
from .ordering import EanCodeOrder


@type(EanCode, filters=EanCodeFilter, order=EanCodeOrder, pagination=True, fields="__all__")
class EanCodeType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
