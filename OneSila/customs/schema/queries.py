from core.schema.queries import node, connection, ListConnectionWithTotalCount, type, field
from customs.models import HsCode


from .types.types import HsCodeType


@type(name="Query")
class CustomsQuery:
    hs_code: HsCodeType = node()
    hs_codes: ListConnectionWithTotalCount[HsCodeType] = connection()
