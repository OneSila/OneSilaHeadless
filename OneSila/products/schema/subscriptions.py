from core.schema.core.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from products.models import Product, BundleProduct, ConfigurableProduct, SimpleProduct, ProductTranslation, \
    ConfigurableVariation, BundleVariation, ManufacturableProduct, DropshipProduct, SupplierProduct, BillOfMaterial
from products.schema.types.types import ProductType, BundleProductType, ConfigurableProductType, \
    SimpleProductType, ProductTranslationType, ConfigurableVariationType, BundleVariationType, ManufacturableProductType, DropshipProductType, \
    SupplierProductType, BillOfMaterialType


@type(name="Subscription")
class ProductsSubscription:
    @subscription
    async def product(self, info: Info, pk: str) -> AsyncGenerator[ProductType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=Product):
            yield i

    @subscription
    async def bundle_product(self, info: Info, pk: str) -> AsyncGenerator[BundleProductType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=BundleProduct):
            yield i

    @subscription
    async def configurable_product(self, info: Info, pk: str) -> AsyncGenerator[ConfigurableProductType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ConfigurableProduct):
            yield i

    @subscription
    async def simple_product(self, info: Info, pk: str) -> AsyncGenerator[SimpleProductType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SimpleProduct):
            yield i

    @subscription
    async def product_translation(self, info: Info, pk: str) -> AsyncGenerator[ProductTranslationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ProductTranslation):
            yield i

    @subscription
    async def configurable_variation(self, info: Info, pk: str) -> AsyncGenerator[ConfigurableVariationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ConfigurableVariation):
            yield i

    @subscription
    async def bundle_variation(self, info: Info, pk: str) -> AsyncGenerator[BundleVariationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=BundleVariation):
            yield i

    @subscription
    async def manufacturable_product(self, info: Info, pk: str) -> AsyncGenerator[ManufacturableProductType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ManufacturableProduct):
            yield i

    @subscription
    async def dropship_product(self, info: Info, pk: str) -> AsyncGenerator[DropshipProductType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=DropshipProduct):
            yield i

    @subscription
    async def supplier_product(self, info: Info, pk: str) -> AsyncGenerator[SupplierProductType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=SupplierProduct):
            yield i

    @subscription
    async def bill_of_material(self, info: Info, pk: str) -> AsyncGenerator[BillOfMaterialType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=BillOfMaterial):
            yield i
