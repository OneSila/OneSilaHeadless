from core.schema.core.types.types import auto
from core.schema.core.types.filters import filter

from customs.models import HsCode


@filter(HsCode)
class HsCodeFilter:
    id: auto
    code: auto
    name: auto
