from collections import defaultdict
from typing import Iterable

from products.models import ProductTranslation, ProductTranslationBulletPoint


class ProductTranslationImportFactory:
    HTML_FIELDS = {"short_description", "description"}
    CONTENT_FIELDS = ("name", "subtitle", "short_description", "description", "url_key")

    def __init__(
        self,
        *,
        multi_tenant_company,
        products: Iterable,
        source_channel,
        target_channel,
        language: str | None,
        override: bool,
        all_languages: bool,
        fields: list[str],
    ) -> None:
        self.multi_tenant_company = multi_tenant_company
        self.products = list(products)
        self.product_ids = [product.id for product in self.products]
        self.source_channel = source_channel
        self.target_channel = target_channel
        self.language = language
        self.override = bool(override)
        self.all_languages = bool(all_languages)
        self.fields = set(fields)
        self.include_bullet_points = "bullet_points" in self.fields
        self.content_fields = [field for field in self.CONTENT_FIELDS if field in self.fields]

    def _get_translation_queryset(self, *, sales_channel):
        queryset = ProductTranslation.objects.filter(
            product_id__in=self.product_ids,
            multi_tenant_company=self.multi_tenant_company,
            sales_channel=sales_channel,
        )

        if not self.all_languages and self.language:
            queryset = queryset.filter(language=self.language)

        if self.include_bullet_points:
            queryset = queryset.prefetch_related("bullet_points")

        return queryset.select_related("product")

    def _build_translation_map(self, *, translations):
        translations_map = defaultdict(dict)
        for translation in translations:
            translations_map[translation.product_id][translation.language] = translation
        return translations_map

    def _normalize_html_value(self, *, value: str | None) -> str:
        if not value:
            return "<p><br></p>"
        trimmed = value.strip()
        return trimmed or "<p><br></p>"

    def _is_empty_html(self, *, value: str | None) -> bool:
        if not value:
            return True
        normalized = "".join(value.split()).lower()
        return normalized in {"<p><br></p>", "<br>", "<p></p>"}

    def _has_value(self, *, field: str, value: str | None) -> bool:
        if field in self.HTML_FIELDS:
            return not self._is_empty_html(value=value)
        return bool(value and value.strip())

    def _normalize_field_value(self, *, field: str, source_value: str | None) -> str:
        if field in self.HTML_FIELDS:
            return self._normalize_html_value(value=source_value)
        return source_value or ""

    def _build_payload(self, *, source, destination):
        payload = {}
        for field in self.content_fields:
            source_value = getattr(source, field, None)
            destination_value = getattr(destination, field, None) if destination else None

            if not self.override:
                if self._has_value(field=field, value=destination_value):
                    continue
                if not self._has_value(field=field, value=source_value):
                    continue

            payload[field] = self._normalize_field_value(field=field, source_value=source_value)

        return payload

    def _update_translation(self, *, destination, payload: dict[str, str]):
        for field, value in payload.items():
            setattr(destination, field, value)
        destination.save(update_fields=list(payload.keys()))

    def _points_have_content(self, *, points) -> bool:
        return any((point.text or "").strip() for point in points)

    def _sync_bullet_points(self, *, source, destination):
        if not self.include_bullet_points or not destination:
            return

        source_points = list(source.bullet_points.all()) if source else []
        destination_points = list(destination.bullet_points.all()) if destination else []
        destination_has_points = self._points_have_content(points=destination_points)

        if not self.override and destination_has_points:
            current_count = len(destination_points)
            if current_count >= 5:
                return

            available_slots = 5 - current_count
            if available_slots <= 0 or not source_points:
                return

            next_sort_order = max((point.sort_order for point in destination_points), default=-1) + 1
            ProductTranslationBulletPoint.objects.bulk_create(
                [
                    ProductTranslationBulletPoint(
                        product_translation=destination,
                        text=point.text,
                        sort_order=next_sort_order + index,
                        multi_tenant_company=self.multi_tenant_company,
                    )
                    for index, point in enumerate(source_points[:available_slots])
                    if (point.text or "").strip()
                ]
            )
            return

        if destination_points:
            ProductTranslationBulletPoint.objects.filter(product_translation=destination).delete()

        if source_points:
            ProductTranslationBulletPoint.objects.bulk_create(
                [
                    ProductTranslationBulletPoint(
                        product_translation=destination,
                        text=point.text,
                        sort_order=point.sort_order,
                        multi_tenant_company=self.multi_tenant_company,
                    )
                    for point in source_points
                ]
            )

    def work(self) -> None:
        if not self.product_ids:
            return

        source_translations = self._get_translation_queryset(sales_channel=self.source_channel)
        destination_translations = self._get_translation_queryset(sales_channel=self.target_channel)

        source_map = self._build_translation_map(translations=source_translations)
        destination_map = self._build_translation_map(translations=destination_translations)

        for product in self.products:
            source_languages = list(source_map.get(product.id, {}).keys())
            if self.all_languages:
                languages = source_languages
            else:
                languages = [self.language] if self.language else []

            for language in languages:
                source_translation = source_map.get(product.id, {}).get(language)
                if not source_translation:
                    continue

                destination_translation = destination_map.get(product.id, {}).get(language)
                payload = self._build_payload(source=source_translation, destination=destination_translation)

                if destination_translation:
                    if payload:
                        self._update_translation(destination=destination_translation, payload=payload)
                else:
                    if not payload or "name" not in payload:
                        continue
                    destination_translation = ProductTranslation.objects.create(
                        product=product,
                        language=language,
                        sales_channel=self.target_channel,
                        multi_tenant_company=self.multi_tenant_company,
                        **payload,
                    )
                    destination_map.setdefault(product.id, {})[language] = destination_translation

                self._sync_bullet_points(source=source_translation, destination=destination_translation)
