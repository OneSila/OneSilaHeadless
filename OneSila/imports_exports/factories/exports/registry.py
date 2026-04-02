from imports_exports.models import Export

from .ean_codes import EanCodesExportFactory
from .media import DocumentsExportFactory, ImagesExportFactory, VideosExportFactory
from .product_properties import ProductPropertiesExportFactory
from .products import ProductsExportFactory
from .properties import (
    PropertiesExportFactory,
    PropertySelectValuesExportFactory,
    RulesExportFactory,
)
from .sales_prices import (
    PriceListPricesExportFactory,
    PriceListsExportFactory,
    SalesPricesExportFactory,
)


EXPORT_FACTORY_REGISTRY = {
    Export.KIND_PRODUCTS: ProductsExportFactory,
    Export.KIND_PRODUCT_PROPERTIES: ProductPropertiesExportFactory,
    Export.KIND_PROPERTIES: PropertiesExportFactory,
    Export.KIND_PROPERTY_SELECT_VALUES: PropertySelectValuesExportFactory,
    Export.KIND_IMAGES: ImagesExportFactory,
    Export.KIND_DOCUMENTS: DocumentsExportFactory,
    Export.KIND_VIDEOS: VideosExportFactory,
    Export.KIND_SALES_PRICES: SalesPricesExportFactory,
    Export.KIND_PRICE_LISTS: PriceListsExportFactory,
    Export.KIND_PRICE_LIST_PRICES: PriceListPricesExportFactory,
    Export.KIND_RULES: RulesExportFactory,
    Export.KIND_EAN_CODES: EanCodesExportFactory,
}


def get_export_factory(*, kind):
    try:
        return EXPORT_FACTORY_REGISTRY[kind]
    except KeyError as exc:
        raise ValueError(f"Unsupported export kind: {kind}") from exc
