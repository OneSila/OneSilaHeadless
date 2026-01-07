from typing import Optional, List as TypingList

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
    ProductVariationsTaskResponse,
    ProductTranslationImportTaskResponse,
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
    ProductPropertiesRulePartialInput,
    PropertySelectValuePartialInput,
    ProductTranslationBulkImportInput,
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
    def generate_product_variations(
        self,
        info: Info,
        rule_product_type: PropertySelectValuePartialInput,
        product: ProductPartialInput,
        select_values: TypingList[PropertySelectValuePartialInput],
        language_code: str | None = None,
    ) -> ProductVariationsTaskResponse:
        from products.tasks import products__generate_variations_task
        from products.models import Product
        from properties.models import ProductPropertiesRule, PropertySelectValue

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        rule_obj = ProductPropertiesRule.objects.get(
            product_type_id=rule_product_type.id.node_id,
            multi_tenant_company=multi_tenant_company,
            sales_channel__isnull=True
        )

        config_product_obj = Product.objects.get(
            id=product.id.node_id,
            multi_tenant_company=multi_tenant_company,
        )

        value_ids = [sv.id.node_id for sv in select_values]
        select_value_ids = list(
            PropertySelectValue.objects.filter(
                id__in=value_ids,
                multi_tenant_company=multi_tenant_company,
            ).values_list("id", flat=True)
        )

        products__generate_variations_task(
            rule_id=rule_obj.id,
            config_product_id=config_product_obj.id,
            select_value_ids=select_value_ids,
            language=language_code,
        )

        return ProductVariationsTaskResponse(success=True)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def import_product_translations(
        self,
        *,
        info: Info,
        instance: ProductTranslationBulkImportInput,
    ) -> ProductTranslationImportTaskResponse:
        from django.core.exceptions import ValidationError
        from sales_channels.models import SalesChannel
        from products.tasks import products__tasks__import_product_translations

        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)

        source_channel = None
        target_channel = None

        if instance.channel_source:
            source_channel = SalesChannel.objects.filter(
                id=instance.channel_source.id.node_id,
                multi_tenant_company=multi_tenant_company,
            ).first()
            if not source_channel:
                raise ValidationError("Invalid source sales channel.")

        if instance.channel_target:
            target_channel = SalesChannel.objects.filter(
                id=instance.channel_target.id.node_id,
                multi_tenant_company=multi_tenant_company,
            ).first()
            if not target_channel:
                raise ValidationError("Invalid target sales channel.")

        if source_channel is None and target_channel is None:
            raise ValidationError("Source and target channels cannot be the same.")

        if source_channel and target_channel and source_channel.id == target_channel.id:
            raise ValidationError("Source and target channels cannot be the same.")

        if not instance.all_languages and not instance.language:
            raise ValidationError("Language is required when allLanguages is false.")

        product_ids = [p.id.node_id for p in instance.products or []]
        products = Product.objects.filter(id__in=product_ids, multi_tenant_company=multi_tenant_company)
        if not products.exists():
            raise ValidationError("No products found.")

        fields = [field.value for field in instance.fields]

        products__tasks__import_product_translations(
            multi_tenant_company_id=multi_tenant_company.id,
            product_ids=list(products.values_list("id", flat=True)),
            source_channel_id=source_channel.id if source_channel else None,
            target_channel_id=target_channel.id if target_channel else None,
            language=instance.language,
            override=instance.override or False,
            all_languages=instance.all_languages or False,
            fields=fields,
        )

        return ProductTranslationImportTaskResponse(success=True)

    @strawberry_django.mutation(handle_django_errors=False, extensions=default_extensions)
    def duplicate_product(
        self,
        info: Info,
        product: ProductPartialInput,
        sku: str | None = None,
        create_as_alias: bool = False,
        create_relationships: bool = True,
    ) -> ProductType:
        multi_tenant_company = get_multi_tenant_company(info, fail_silently=False)
        try:
            instance = Product.objects.get(
                id=product.id.node_id,
                multi_tenant_company=multi_tenant_company,
            )
        except Product.DoesNotExist:
            raise PermissionError("Invalid company")
        duplicated = Product.objects.duplicate_product(
            instance,
            sku=sku,
            create_as_alias=create_as_alias,
            create_relationships=create_relationships,
        )
        return duplicated
