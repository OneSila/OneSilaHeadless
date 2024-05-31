from core.schema.core.mutations import create, update, delete, type, List
from .fields import create_product
from ..types.types import ProductType, BundleProductType, UmbrellaProductType, \
    SimpleProductType, ProductTranslationType, UmbrellaVariationType, \
    BundleVariationType
from ..types.input import ProductInput, BundleProductInput, UmbrellaProductInput, \
    SimpleProductInput, ProductTranslationInput, UmbrellaVariationInput, \
    BundleVariationInput, ProductPartialInput, UmbrellaProductPartialInput, \
    BundleProductPartialInput, SimpleProductPartialInput, \
    ProductTranslationPartialInput, UmbrellaVariationPartialInput, \
    BundleVariationPartialInput



@type(name="Mutation")
class ProductsMutation:
    create_product: ProductType = create_product()
    create_products: List[ProductType] = create(ProductInput)
    update_product: ProductType = update(ProductPartialInput)
    delete_product: ProductType = delete()
    delete_products: List[ProductType] = delete()

    create_bundle_product: BundleProductType = create(BundleProductInput)
    create_bundle_products: List[BundleProductType] = create(BundleProductInput)
    update_bundle_product: BundleProductType = update(BundleProductPartialInput)
    delete_bundle_product: BundleProductType = delete()
    delete_bundle_products: List[BundleProductType] = delete()

    create_umbrella_product: UmbrellaProductType = create(UmbrellaProductInput)
    create_umbrella_products: List[UmbrellaProductType] = create(UmbrellaProductInput)
    update_umbrella_product: UmbrellaProductType = update(UmbrellaProductPartialInput)
    delete_umbrella_product: UmbrellaProductType = delete()
    delete_umbrella_products: List[UmbrellaProductType] = delete()

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

    create_umbrella_variation: UmbrellaVariationType = create(UmbrellaVariationInput)
    create_umbrella_variations: List[UmbrellaVariationType] = create(UmbrellaVariationInput)
    update_umbrella_variation: UmbrellaVariationType = update(UmbrellaVariationPartialInput)
    delete_umbrella_variation: UmbrellaVariationType = delete()
    delete_umbrella_variations: List[UmbrellaVariationType] = delete()

    create_bundle_variation: BundleVariationType = create(BundleVariationInput)
    create_bundle_variations: List[BundleVariationType] = create(BundleVariationInput)
    update_bundle_variation: BundleVariationType = update(BundleVariationPartialInput)
    delete_bundle_variation: BundleVariationType = delete()
    delete_bundle_variations: List[BundleVariationType] = delete()
