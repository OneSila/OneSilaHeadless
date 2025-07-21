from .fields import create_product
from strawberry import Info
import strawberry_django
from core.schema.core.extensions import default_extensions
from core.schema.core.helpers import get_multi_tenant_company
from products.models import Product
from ..types.types import (
    ProductType,
    BundleProductType,
    ConfigurableProductType,
    SimpleProductType,
    ProductTranslationType,
    ConfigurableVariationType,
    BundleVariationType,
    ProductTranslationBulletPointType,
)
from ..types.input import (
    ProductInput,
    BundleProductInput,
    ConfigurableProductInput,
    SimpleProductInput,
    ProductTranslationInput,
    ConfigurableVariationInput,
    BundleVariationInput,
    ProductPartialInput,
    ConfigurableProductPartialInput,
    BundleProductPartialInput,
    SimpleProductPartialInput,
    ProductTranslationPartialInput,
    ConfigurableVariationPartialInput,
    BundleVariationPartialInput,
    ProductTranslationBulletPointInput,
    ProductTranslationBulletPointPartialInput,
)
from core.schema.core.mutations import create, update, delete, type, List


@type(name="Mutation")
class ProductsMutation:
    create_product: ProductType = create_product()
    create_products: List[ProductType] = create(ProductInput)
    update_product: ProductType = update(ProductPartialInput)
    delete_product: ProductType = delete()
    delete_products: List[ProductType] = delete(is_bulk=True)

    create_bundle_product: BundleProductType = create(BundleProductInput)
    create_bundle_products: List[BundleProductType] = create(BundleProductInput)
    update_bundle_product: BundleProductType = update(BundleProductPartialInput)
    delete_bundle_product: BundleProductType = delete()
    delete_bundle_products: List[BundleProductType] = delete()

    create_configurable_product: ConfigurableProductType = create(ConfigurableProductInput)
    create_configurable_products: List[ConfigurableProductType] = create(ConfigurableProductInput)
    update_configurable_product: ConfigurableProductType = update(ConfigurableProductPartialInput)
    delete_configurable_product: ConfigurableProductType = delete()
    delete_configurable_products: List[ConfigurableProductType] = delete()

    create_simple_product: SimpleProductType = create(SimpleProductInput)
    create_simple_products: List[SimpleProductType] = create(SimpleProductInput)
    update_simple_product: SimpleProductType = update(SimpleProductPartialInput)
    delete_simple_product: SimpleProductType = delete()
    delete_simple_products: List[SimpleProductType] = delete()

    create_product_translation: ProductTranslationType = create(ProductTranslationInput)
    create_product_translations: List[ProductTranslationType] = create(ProductTranslationInput)
    update_product_translation: ProductTranslationType = update(ProductTranslationPartialInput)
    delete_product_translation: ProductTranslationType = delete()
    delete_product_translations: List[ProductTranslationType] = delete()

    create_configurable_variation: ConfigurableVariationType = create(ConfigurableVariationInput)
    create_configurable_variations: List[ConfigurableVariationType] = create(List[ConfigurableVariationInput])
    update_configurable_variation: ConfigurableVariationType = update(ConfigurableVariationPartialInput)
    delete_configurable_variation: ConfigurableVariationType = delete()
    delete_configurable_variations: List[ConfigurableVariationType] = delete()

    create_bundle_variation: BundleVariationType = create(BundleVariationInput)
    create_bundle_variations: List[BundleVariationType] = create(List[BundleVariationInput])
    update_bundle_variation: BundleVariationType = update(BundleVariationPartialInput)
    delete_bundle_variation: BundleVariationType = delete()
    delete_bundle_variations: List[BundleVariationType] = delete()

    create_product_translation_bullet_point: ProductTranslationBulletPointType = create(ProductTranslationBulletPointInput)
    create_product_translation_bullet_points: List[ProductTranslationBulletPointType] = create(List[ProductTranslationBulletPointInput])
    update_product_translation_bullet_point: ProductTranslationBulletPointType = update(ProductTranslationBulletPointPartialInput)
    delete_product_translation_bullet_point: ProductTranslationBulletPointType = delete()
    delete_product_translation_bullet_points: List[ProductTranslationBulletPointType] = delete(is_bulk=True)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def duplicate_product(self, info: Info, product: ProductPartialInput, sku: str | None = None) -> ProductType:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        instance =  Product.objects.get(id=product.id.node_id)
        if instance.multi_tenant_company != multi_tenant_company:
            raise PermissionError("Invalid company")
        duplicated = Product.objects.duplicate_product(instance, sku=sku)
        return duplicated
