from core.schema.types.types import relay, type, GetQuerysetMultiTenantMixin

from typing import List

from units.models import Unit
from .filters import UnitFilter
from .ordering import UnitOrder


@type(Unit, filters=UnitFilter, order=UnitOrder, pagination=True, fields="__all__")
class UnitType(relay.Node, GetQuerysetMultiTenantMixin):
    pass
