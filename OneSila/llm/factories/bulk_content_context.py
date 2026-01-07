from collections import defaultdict
from typing import Any

from django.conf import settings
from llm.models import BrandCustomPrompt
from media.models import Media, MediaProductThrough
from products.models import ConfigurableVariation, Product, ProductTranslation
from properties.models import ProductProperty, Property


class BulkContentContextBuilder:
    MAX_VARIATIONS_CONTEXT = 10
    def __init__(
        self,
        *,
        multi_tenant_company,
        products: list[Product],
        default_language: str,
    ):
        self.multi_tenant_company = multi_tenant_company
        self.products = products
        self.default_language = default_language
        self.translations_by_product: dict[int, list[ProductTranslation]] = {}
        self.variations_by_parent: dict[int, list[Product]] = {}
        self.property_map: dict[int, dict[str, list[str]]] = {}
        self.brand_prompts: dict[int, dict[str | None, str]] = {}
        self.media_map: dict[int, dict[str, list[str]]] = {}

    def build(self) -> None:
        self.translations_by_product = {
            product.id: list(product.translations.all()) for product in self.products
        }
        self._load_variations()
        self._build_property_map()
        self._build_brand_prompts()
        self._build_media_map()

    def _load_variations(self) -> None:
        parent_ids = [product.id for product in self.products if product.is_configurable()]
        if not parent_ids:
            return

        variations = (
            ConfigurableVariation.objects.filter(parent_id__in=parent_ids)
            .values_list("parent_id", "variation_id")
        )
        variation_map: dict[int, list[int]] = defaultdict(list)
        variation_ids: set[int] = set()
        for parent_id, variation_id in variations:
            variation_map[parent_id].append(variation_id)
            variation_ids.add(variation_id)

        if not variation_ids:
            return

        variation_products = Product.objects.filter(id__in=variation_ids)
        variation_lookup = {product.id: product for product in variation_products}

        for parent_id, variation_ids_list in variation_map.items():
            self.variations_by_parent[parent_id] = [
                variation_lookup[var_id] for var_id in variation_ids_list if var_id in variation_lookup
            ]

    def _build_property_map(self) -> None:
        product_ids = {product.id for product in self.products}
        for variations in self.variations_by_parent.values():
            product_ids.update([variation.id for variation in variations])

        if not product_ids:
            return

        properties = (
            ProductProperty.objects.filter(product_id__in=product_ids)
            .select_related("property", "value_select")
            .prefetch_related("value_multi_select", "productpropertytexttranslation_set")
        )

        property_map: dict[int, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

        for prop in properties:
            prop_type = prop.property.type
            prop_name = str(prop.property.name)
            if prop_type == Property.TYPES.MULTISELECT:
                values = {value.value for value in prop.value_multi_select.all()}
            elif prop_type == Property.TYPES.SELECT:
                values = {prop.value_select.value} if prop.value_select else set()
            elif prop_type in {Property.TYPES.TEXT, Property.TYPES.DESCRIPTION}:
                value = prop.get_value_text() if prop_type == Property.TYPES.TEXT else prop.get_value_description()
                values = {str(value)} if value not in (None, "") else set()
            elif prop_type in {
                Property.TYPES.INT,
                Property.TYPES.FLOAT,
                Property.TYPES.BOOLEAN,
                Property.TYPES.DATE,
                Property.TYPES.DATETIME,
            }:
                value = prop.get_value()
                values = {str(value)} if value not in (None, "") else set()
            else:
                values = set()

            property_map[prop.product_id][prop_name].update(values)

        self.property_map = {
            product_id: {name: sorted(values) for name, values in props.items()}
            for product_id, props in property_map.items()
        }

    def _build_brand_prompts(self) -> None:
        brand_props = (
            ProductProperty.objects.filter(
                product_id__in=[product.id for product in self.products],
                property__internal_name="brand",
            )
            .select_related("value_select")
        )
        brand_value_ids = {prop.value_select_id for prop in brand_props if prop.value_select_id}
        if not brand_value_ids:
            return

        prompts = BrandCustomPrompt.objects.filter(
            brand_value_id__in=brand_value_ids,
            multi_tenant_company=self.multi_tenant_company,
        )

        prompt_map: dict[int, dict[str | None, str]] = defaultdict(dict)
        for prompt in prompts:
            prompt_map[prompt.brand_value_id][prompt.language] = prompt.prompt

        for prop in brand_props:
            brand_value_id = prop.value_select_id
            if not brand_value_id:
                continue
            self.brand_prompts[prop.product_id] = prompt_map.get(brand_value_id, {})

    def _build_media_map(self) -> None:
        if settings.DEBUG:
            return

        media_qs = (
            MediaProductThrough.objects.filter(
                product_id__in=[product.id for product in self.products],
                sales_channel__isnull=True,
            )
            .select_related("media")
        )

        media_map: dict[int, dict[str, list[str]]] = defaultdict(lambda: {"images": [], "documents": []})
        for item in media_qs:
            if item.media.type == Media.IMAGE and item.media.image_url():
                media_map[item.product_id]["images"].append(item.media.image_url())
            elif item.media.type == Media.FILE and item.media.file_url():
                media_map[item.product_id]["documents"].append(item.media.file_url())

        self.media_map = media_map

    @staticmethod
    def select_translation(
        *,
        translations: list[ProductTranslation],
        language: str,
        sales_channel_id: int | None,
    ) -> ProductTranslation | None:

        if sales_channel_id is None:
            for translation in translations:
                if translation.language == language and translation.sales_channel_id is None:
                    return translation
        else:
            for translation in translations:
                if translation.language == language and translation.sales_channel_id == sales_channel_id:
                    return translation

        return None

    def build_existing_content(
        self,
        *,
        translations: list[ProductTranslation],
        language: str,
        sales_channel_id: int | None,
    ) -> dict[str, Any]:
        translation = self.select_translation(
            translations=translations,
            language=language,
            sales_channel_id=sales_channel_id,
        )
        if not translation:
            return {}

        bullets = sorted(list(translation.bullet_points.all()), key=lambda item: item.sort_order)
        bullet_points = [bullet.text for bullet in bullets]

        return {
            "name": translation.name,
            "subtitle": translation.subtitle,
            "shortDescription": translation.short_description,
            "description": translation.description,
            "urlKey": translation.url_key,
            "bulletPoints": bullet_points,
        }

    def build_product_context(
        self,
        *,
        product: Product,
        languages: list[str],
        default_language: str | None = None,
        sales_channel_id: int | None = None,
    ) -> dict[str, Any]:
        default_language = default_language or self.default_language
        translations = self.translations_by_product.get(product.id, [])
        default_translation = self.select_translation(
            translations=translations,
            language=default_language,
            sales_channel_id=sales_channel_id,
        )

        base_properties = self.property_map.get(product.id, {})
        is_configurable = product.is_configurable()
        properties_payload: dict[str, Any]

        if is_configurable:
            variations_payload = []
            aggregate_properties: dict[str, set[str]] = defaultdict(set)
            for name, values in base_properties.items():
                aggregate_properties[name].update(values)

            variations = sorted(
                self.variations_by_parent.get(product.id, []),
                key=lambda item: str(item.sku or item.id),
            )[:self.MAX_VARIATIONS_CONTEXT]
            for variation in variations:
                variation_properties = self.property_map.get(variation.id, {})
                for name, values in variation_properties.items():
                    aggregate_properties[name].update(values)
                variations_payload.append(
                    {
                        "sku": variation.sku,
                    }
                )
            common_properties = {name: sorted(values) for name, values in aggregate_properties.items()}
            properties_payload = {
                "common": common_properties,
                "variations": variations_payload,
            }
        else:
            properties_payload = base_properties

        media = self.media_map.get(product.id, {"images": [], "documents": []})
        brand_map = self.brand_prompts.get(product.id, {})
        brand_prompt_default = brand_map.get(default_language) or brand_map.get(None)
        brand_prompt_by_language = {}
        for language in languages:
            prompt = brand_map.get(language) or brand_prompt_default
            if prompt:
                brand_prompt_by_language[language] = prompt

        return {
            "product": {
                "id": product.id,
                "sku": product.sku,
                "type": product.type,
                "default_name": default_translation.name if default_translation else "",
                "default_short_description": default_translation.short_description if default_translation else "",
                "default_description": default_translation.description if default_translation else "",
            },
            "properties": properties_payload,
            "brand_prompt_by_language": brand_prompt_by_language,
            "brand_prompt_default": brand_prompt_default,
            "media": media,
        }
