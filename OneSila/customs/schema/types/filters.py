from core.schema.types.types import auto
from core.schema.types.filters import filter

from customs.models import HsCode


@filter(HsCode)
class HsCodeFilter:
    id: auto
    code: auto
    name: auto
