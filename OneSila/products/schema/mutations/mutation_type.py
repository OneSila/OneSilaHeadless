import strawberry_django
from strawberry.relay import from_base64

from core.schema.core.extensions import default_extensions
from .fields import create_product
from ..types.types import ProductType, BundleProductType, ConfigurableProductType, \
    SimpleProductType, ProductTranslationType, ConfigurableVariationType, \
    BundleVariationType, AiContent
from ..types.input import ProductInput, BundleProductInput, ConfigurableProductInput, \
    SimpleProductInput, ProductTranslationInput, ConfigurableVariationInput, \
    BundleVariationInput, ProductPartialInput, ConfigurableProductPartialInput, \
    BundleProductPartialInput, SimpleProductPartialInput, \
    ProductTranslationPartialInput, ConfigurableVariationPartialInput, \
    BundleVariationPartialInput, ProductAiContentInput
from core.schema.core.mutations import create, update, delete, type, List


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
    create_configurable_variations: List[ConfigurableVariationType] = create(ConfigurableVariationInput)
    update_configurable_variation: ConfigurableVariationType = update(ConfigurableVariationPartialInput)
    delete_configurable_variation: ConfigurableVariationType = delete()
    delete_configurable_variations: List[ConfigurableVariationType] = delete()

    create_bundle_variation: BundleVariationType = create(BundleVariationInput)
    create_bundle_variations: List[BundleVariationType] = create(BundleVariationInput)
    update_bundle_variation: BundleVariationType = update(BundleVariationPartialInput)
    delete_bundle_variation: BundleVariationType = delete()
    delete_bundle_variations: List[BundleVariationType] = delete()

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def generate_product_ai_content(self, instance: ProductAiContentInput) -> AiContent:
        from products.models import Product
        from products.flows.generate_prompt import AIGenerateContentFlow

        language = instance.language
        product = Product.objects.get(id=instance.id.node_id)

        content_generator = AIGenerateContentFlow(product=product, language=language)
        content_generator.flow()

        return AiContent(content=content_generator.generated_content, points=content_generator.used_points)