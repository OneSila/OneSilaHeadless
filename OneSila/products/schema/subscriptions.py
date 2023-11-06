from core.schema.subscriptions import type, subscription, Info, AsyncGenerator, model_subscriber

from products.models import Product, BundleProduct, UmbrellaProduct, ProductVariation, ProductTranslation, \
    UmbrellaVariation, BundleVariation
from products.schema.types.types import ProductType, BundleProductType, UmbrellaProductType, \
    ProductVariationType, ProductTranslationType, UmbrellaVariationType, BundleVariationType


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
    async def umbrella_product(self, info: Info, pk: str) -> AsyncGenerator[UmbrellaProductType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=UmbrellaProduct):
            yield i

    @subscription
    async def product_variation(self, info: Info, pk: str) -> AsyncGenerator[ProductVariationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ProductVariation):
            yield i

    @subscription
    async def product_translation(self, info: Info, pk: str) -> AsyncGenerator[ProductTranslationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=ProductTranslation):
            yield i

    @subscription
    async def umbrella_variation(self, info: Info, pk: str) -> AsyncGenerator[UmbrellaVariationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=UmbrellaVariation):
            yield i

    @subscription
    async def bundle_variation(self, info: Info, pk: str) -> AsyncGenerator[BundleVariationType, None]:
        async for i in model_subscriber(info=info, pk=pk, model=BundleVariation):
            yield i
