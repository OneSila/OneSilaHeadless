from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Q
from django.utils.text import slugify

from integrations.constants import INTEGRATIONS_TYPES_MAP
from llm.factories.bulk_content import (
    BulkContentLLM,
    REQUIRED_BULLET_POINTS,
    build_field_rules,
    is_empty_value,
    normalize_bullet_points,
)
from llm.factories.bulk_content_context import BulkContentContextBuilder
from products.models import Product, ProductTranslation, ProductTranslationBulletPoint
from sales_channels.models import SalesChannel


class BulkGenerateContentFlow:
    def __init__(
        self,
        *,
        multi_tenant_company,
        product_ids: list[int | str],
        sales_channel_languages: dict[int | str, list[str]],
        sales_channel_defaults: dict[int | str, str],
        override: bool,
        preview: bool,
        additional_informations: str | None = None,
        debug: bool = False,
    ):
        self.multi_tenant_company = multi_tenant_company
        self.product_ids = product_ids
        self.sales_channel_languages = {
            int(channel_id): list(dict.fromkeys(languages))
            for channel_id, languages in sales_channel_languages.items()
        }
        self.sales_channel_defaults = {
            int(channel_id): language for channel_id, language in sales_channel_defaults.items()
        }
        self.override = override
        self.preview = preview
        self.additional_informations = additional_informations
        self.debug = debug
        self.default_language = multi_tenant_company.language
        self.used_points = 0
        self.preview_payload: dict[str, dict[str, dict[str, Any]]] = {}

        self.sales_channels: list[SalesChannel] = []
        self.products: list[Product] = []
        self.context_builder: BulkContentContextBuilder | None = None

    def _load_sales_channels(self) -> None:
        self.sales_channels = list(
            SalesChannel.objects.filter(
                id__in=list(self.sales_channel_languages.keys()),
                multi_tenant_company=self.multi_tenant_company,
            )
        )
        if not self.sales_channels:
            raise ValidationError("No valid sales channels provided.")

    def _load_products(self) -> None:
        languages = set()
        for language_list in self.sales_channel_languages.values():
            languages.update(language_list)
        languages.add(self.default_language)

        translation_qs = (
            ProductTranslation.objects.filter(language__in=languages)
            .filter(Q(sales_channel__in=self.sales_channels) | Q(sales_channel__isnull=True))
            .select_related("sales_channel")
            .prefetch_related("bullet_points")
        )

        products = (
            Product.objects.filter(id__in=self.product_ids, multi_tenant_company=self.multi_tenant_company)
            .prefetch_related(Prefetch("translations", queryset=translation_qs))
        )
        self.products = list(products)
        if not self.products:
            raise ValidationError("No valid products provided.")

    def _language_needs_generation(self, *, existing: dict[str, Any], field_rules: dict[str, Any]) -> bool:
        for field, enabled in field_rules["flags"].items():
            if not enabled or field == "urlKey":
                continue
            if field == "bulletPoints":
                bullet_points = existing.get("bulletPoints", []) if existing else []
                if len(bullet_points) < REQUIRED_BULLET_POINTS:
                    return True
                continue
            if is_empty_value(value=existing.get(field)):
                return True
        return False

    def _merge_bullet_points(
        self,
        *,
        existing: list[str],
        generated: list[str],
        override: bool,
    ) -> list[str]:
        if override:
            return generated[:REQUIRED_BULLET_POINTS]

        if len(existing) >= REQUIRED_BULLET_POINTS:
            return existing[:REQUIRED_BULLET_POINTS]

        existing_norm = {text.strip().lower() for text in existing}
        merged = list(existing)
        for point in generated:
            if point.strip().lower() in existing_norm:
                continue
            merged.append(point)
            existing_norm.add(point.strip().lower())
            if len(merged) >= REQUIRED_BULLET_POINTS:
                break

        return merged[:REQUIRED_BULLET_POINTS]

    def _build_url_key(self, *, name: str, max_len: int | None) -> str | None:
        if not name:
            return None
        url_key = slugify(name)
        if max_len:
            url_key = url_key[:max_len]
        return url_key

    def _merge_language_content(
        self,
        *,
        existing: dict[str, Any],
        generated: dict[str, Any],
        field_rules: dict[str, Any],
        override: bool,
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {}

        for field in ("name", "subtitle", "shortDescription", "description"):
            if not field_rules["flags"].get(field, False):
                continue
            if override or is_empty_value(value=existing.get(field)):
                merged[field] = generated.get(field)
            else:
                merged[field] = existing.get(field)

        if field_rules["flags"].get("bulletPoints", False):
            merged["bulletPoints"] = self._merge_bullet_points(
                existing=existing.get("bulletPoints", []),
                generated=normalize_bullet_points(value=generated.get("bulletPoints", [])),
                override=override,
            )

        if field_rules["flags"].get("urlKey", False):
            url_key_limit = field_rules["limits"].get("urlKey", {}).get("max")
            max_len = url_key_limit if url_key_limit and url_key_limit > 0 else None
            name_value = merged.get("name") or existing.get("name") or ""
            url_key = self._build_url_key(name=name_value, max_len=max_len)
            if override or is_empty_value(value=existing.get("urlKey")):
                merged["urlKey"] = url_key
            else:
                merged["urlKey"] = existing.get("urlKey")

        return merged

    def _apply_bullet_points(
        self,
        *,
        translation: ProductTranslation,
        points: list[str],
        override: bool,
    ) -> None:
        if override:
            translation.bullet_points.all().delete()
            points_to_create = points[:REQUIRED_BULLET_POINTS]
            ProductTranslationBulletPoint.objects.bulk_create(
                [
                    ProductTranslationBulletPoint(
                        product_translation=translation,
                        text=point,
                        sort_order=index,
                    )
                    for index, point in enumerate(points_to_create)
                ]
            )
            return

        existing_points = list(translation.bullet_points.all())
        if len(existing_points) >= REQUIRED_BULLET_POINTS:
            return

        start_index = len(existing_points)
        ProductTranslationBulletPoint.objects.bulk_create(
            [
                ProductTranslationBulletPoint(
                    product_translation=translation,
                    text=point,
                    sort_order=start_index + index,
                )
                for index, point in enumerate(points[start_index:REQUIRED_BULLET_POINTS])
            ]
        )

    def _save_language_content(
        self,
        *,
        product: Product,
        sales_channel: SalesChannel,
        language: str,
        merged: dict[str, Any],
    ) -> None:
        translation = self.context_builder.select_translation(
            translations=self.context_builder.translations_by_product.get(product.id, []),
            language=language,
            sales_channel_id=sales_channel.id,
        )

        if not translation:
            translation = ProductTranslation(
                product=product,
                language=language,
                sales_channel=sales_channel,
                name=merged.get("name") or product.sku or "",
            )

        for field, attr in {
            "name": "name",
            "subtitle": "subtitle",
            "shortDescription": "short_description",
            "description": "description",
            "urlKey": "url_key",
        }.items():
            if field in merged:
                setattr(translation, attr, merged.get(field))

        translation.save()

        if "bulletPoints" in merged:
            self._apply_bullet_points(
                translation=translation,
                points=merged.get("bulletPoints", []),
                override=self.override,
            )

    def _process_product_sales_channel(
        self,
        *,
        product: Product,
        sales_channel: SalesChannel,
        field_rules: dict[str, Any],
        integration_type: str,
    ) -> None:
        if not self.context_builder:
            raise ValidationError("Content context not initialized.")

        translations = self.context_builder.translations_by_product.get(product.id, [])
        languages = self.sales_channel_languages.get(sales_channel.id, [])
        if not languages:
            raise ValidationError("Languages missing for sales channel.")
        existing_by_language = {
            language: self.context_builder.build_existing_content(
                translations=translations,
                language=language,
                sales_channel_id=sales_channel.id,
            )
            for language in languages
        }
        channel_default = self.sales_channel_defaults.get(sales_channel.id, self.default_language)
        default_existing = self.context_builder.build_existing_content(
            translations=translations,
            language=channel_default,
            sales_channel_id=sales_channel.id,
        )

        if self.override:
            languages_to_generate = list(languages)
        else:
            languages_to_generate = [
                language
                for language in languages
                if self._language_needs_generation(
                    existing=existing_by_language.get(language, {}),
                    field_rules=field_rules,
                )
            ]

        generated_by_language: dict[str, dict[str, Any]] = {}
        if languages_to_generate:
            llm_factory = BulkContentLLM(
                product=product,
                sales_channel=sales_channel,
                integration_type=integration_type,
                languages=languages_to_generate,
                field_rules=field_rules,
                product_context=self.context_builder.build_product_context(
                    product=product,
                    languages=languages,
                    default_language=channel_default,
                ),
                existing_content={
                    **existing_by_language,
                    channel_default: default_existing,
                },
                default_language=channel_default,
                additional_informations=self.additional_informations,
                debug=self.debug,
            )
            generated_by_language = llm_factory.generate_content()
            self.used_points += llm_factory.used_points

        for language in languages:
            existing = existing_by_language.get(language, {})
            generated = generated_by_language.get(language, {})
            merged = self._merge_language_content(
                existing=existing,
                generated=generated,
                field_rules=field_rules,
                override=self.override,
            )

            if self.preview:
                integration_key = getattr(sales_channel, "global_id", None) or str(sales_channel.id)
                product_key = str(product.sku or product.id)
                self.preview_payload.setdefault(integration_key, {}).setdefault(product_key, {})[language] = merged
            else:
                if merged:
                    self._save_language_content(
                        product=product,
                        sales_channel=sales_channel,
                        language=language,
                        merged=merged,
                    )

    def flow(self) -> dict[str, Any]:
        self._load_sales_channels()
        self._load_products()
        self.context_builder = BulkContentContextBuilder(
            multi_tenant_company=self.multi_tenant_company,
            products=self.products,
            default_language=self.default_language,
        )
        self.context_builder.build()

        for product in self.products:
            for sales_channel in self.sales_channels:
                integration_type = INTEGRATIONS_TYPES_MAP.get(type(sales_channel), "default")
                field_rules = build_field_rules(integration_type=integration_type)
                self._process_product_sales_channel(
                    product=product,
                    sales_channel=sales_channel,
                    field_rules=field_rules,
                    integration_type=integration_type,
                )

        if self.preview:
            return [
                {integration_id: payload} for integration_id, payload in self.preview_payload.items()
            ]
        return {}
