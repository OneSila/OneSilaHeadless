from core.schema.mutations import type
from core.schema.mutations import create, update, delete, type, List

from .types.types import SalesPriceType, SalesPriceListType, SalesPriceListItemType
from .types.input import SalesPriceInput, SalesPriceListInput, SalesPriceListItemInput, \
    SalesPricePartialInput, SalesPriceListPartialInput, SalesPriceListItemPartialInput


@type(name="Mutation")
class Mutation:
    create_: SalesPriceType = create(SalesPriceInput)
    create_: List[SalesPriceType] = create(SalesPriceInput)
    update_: SalesPriceType = update(SalesPricePartialInput)
    delete_: SalesPriceType = delete()
    delete_: List[SalesPriceType] = delete()

    create_: SalesPriceListType = create(SalesPriceListInput)
    create_: List[SalesPriceListType] = create(SalesPriceListInput)
    update_: SalesPriceListType = update(SalesPriceListPartialInput)
    delete_: SalesPriceListType = delete()
    delete_: List[SalesPriceListType] = delete()

    create_: SalesPriceListItemType = create(SalesPriceListItemInput)
    create_: List[SalesPriceListItemType] = create(SalesPriceListItemInput)
    update_: SalesPriceListItemType = update(SalesPriceListItemPartialInput)
    delete_: SalesPriceListItemType = delete()
    delete_: List[SalesPriceListItemType] = delete()
