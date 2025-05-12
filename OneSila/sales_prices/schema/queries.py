from core.schema.core.queries import node, connection, DjangoListConnection, \
    type

from .types.types import SalesPriceType, SalesPriceListType, SalesPriceListItemType


@type(name="Query")
class SalesPricesQuery:
    sales_price: SalesPriceType = node()
    sales_prices: DjangoListConnection[SalesPriceType] = connection()

    sales_price_list: SalesPriceListType = node()
    sales_price_lists: DjangoListConnection[SalesPriceListType] = connection()

    sales_price_list_item: SalesPriceListItemType = node()
    sales_price_list_items: DjangoListConnection[SalesPriceListItemType] = connection()
