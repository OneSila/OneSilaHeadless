from core.schema.queries import node, connection, ListConnectionWithTotalCount, type
from typing import List

from .types.types import SalesPriceType, SalesPriceListType, SalesPriceListItemType


@type(name="Query")
class SalesPricesQuery:
    sales_price: SalesPriceType = node()
    sales_prices: ListConnectionWithTotalCount[SalesPriceType] = connection()

    sales_price_list: SalesPriceListType = node()
    sales_price_lists: ListConnectionWithTotalCount[SalesPriceListType] = connection()

    sales_price_list_item: SalesPriceListItemType = node()
    sales_price_list_items: ListConnectionWithTotalCount[SalesPriceListItemType] = connection()
