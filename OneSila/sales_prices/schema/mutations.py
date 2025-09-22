from core.schema.core.mutations import type
from core.schema.core.mutations import create, update, delete, type, List

from .types.types import SalesPriceType, SalesPriceListType, SalesPriceListItemType
from .types.input import SalesPriceInput, SalesPriceListInput, SalesPriceListItemInput, \
    SalesPricePartialInput, SalesPriceListPartialInput, SalesPriceListItemPartialInput


@type(name="Mutation")
class SalesPricesMutation:
    create_sales_price: SalesPriceType = create(SalesPriceInput)
    create_sales_prices: List[SalesPriceType] = create(List[SalesPriceInput])
    update_sales_price: SalesPriceType = update(SalesPricePartialInput)
    delete_sales_price: SalesPriceType = delete()
    delete_sales_prices: List[SalesPriceType] = delete()

    create_sales_price_list: SalesPriceListType = create(SalesPriceListInput)
    create_sales_price_lists: List[SalesPriceListType] = create(SalesPriceListInput)
    update_sales_price_list: SalesPriceListType = update(SalesPriceListPartialInput)
    delete_sales_price_list: SalesPriceListType = delete()
    delete_sales_price_lists: List[SalesPriceListType] = delete(is_bulk=True)

    create_sales_price_list_item: SalesPriceListItemType = create(SalesPriceListItemInput)
    create_sales_price_list_items: List[SalesPriceListItemType] = create(SalesPriceListItemInput)
    update_sales_price_list_item: SalesPriceListItemType = update(SalesPriceListItemPartialInput)
    delete_sales_price_list_item: SalesPriceListItemType = delete()
    delete_sales_price_list_items: List[SalesPriceListItemType] = delete()
