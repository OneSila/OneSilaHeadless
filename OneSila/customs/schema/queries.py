from core.schema.core.queries import node, connection, DjangoListConnection, type

from .types.types import HsCodeType


@type(name="Query")
class CustomsQuery:
    hs_code: HsCodeType = node()
    hs_codes: DjangoListConnection[HsCodeType] = connection()
