from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError

from properties.models import ProductProperty
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklProductCategory,
    MiraklProductType,
    MiraklProperty,
    MiraklPropertySelectValue,
    MiraklPublicDefinition,
)
from sales_channels.models import SalesChannelFeedItem

from .context import MiraklProductSourceDataLoader
from .headers import get_mirakl_category_header_properties


class _BaseMiraklProductPayloadFactory:
    action = SalesChannelFeedItem.ACTION_UPDATE

    def __init__(self, *, remote_product, sales_channel_view=None) -> None:
        self.remote_product = remote_product
        self.sales_channel = remote_product.sales_channel
        self.local_product = remote_product.local_instance
        self.language = getattr(self.sales_channel.multi_tenant_company, "language", None)
        self.sales_channel_view = sales_channel_view
        self.source_data_loader = MiraklProductSourceDataLoader(remote_product=remote_product)
        self._category_cache: dict[str, MiraklCategory | None] = {}
        self._product_type_cache: dict[str, MiraklProductType | None] = {}
        self._public_definition_cache: dict[str, MiraklPublicDefinition | None] = {}

    def build(self) -> list[dict[str, Any]]:
        if self.local_product is None:
            return []

        products = self.source_data_loader.resolve_products()
        translations = self.source_data_loader.load_translations(products=products)
        product_properties_by_product = self.source_data_loader.load_properties(products=products)
        prices = self.source_data_loader.load_prices(products=products)
        media = self.source_data_loader.load_media(products=products)
        eans = self.source_data_loader.load_eans(products=products)

        parent_sku = getattr(self.local_product, "sku", "") or ""
        variant_group_code = parent_sku if self.local_product.is_configurable() else ""
        payloads: list[dict[str, Any]] = []

        for product in products:
            translation = self.source_data_loader.select_translation(translations=translations.get(product.id, []))
            product_properties = list(product_properties_by_product.get(product.id, []))
            product_context = self._build_product_context(
                product=product,
                translation=translation,
                product_properties=product_properties,
                prices=list(prices.get(product.id, [])),
                images=list(media.get(product.id, [])),
                ean=eans.get(product.id, ""),
                parent_sku=parent_sku,
                variant_group_code=variant_group_code,
            )

            header_properties = self._get_header_properties(
                category=product_context["category"],
                sales_channel_view=self.sales_channel_view,
            )
            row = self._build_header_row(
                product_context=product_context,
                header_properties=header_properties,
            )
            row.update(
                {
                    "local_product_id": product.id,
                    "action": self.action,
                    "sku": product_context["sku"],
                    "parent_sku": product_context["parent_sku"],
                    "variant_group_code": product_context["variant_group_code"],
                    "type": getattr(product, "type", "") or "",
                    "active": bool(getattr(product, "active", False)),
                    "name": product_context["name"],
                    "short_description": product_context["short_description"],
                    "description": product_context["description"],
                    "url_key": product_context["url_key"],
                    "ean": product_context["ean"],
                    "images": product_context["images"],
                    "prices": product_context["prices"],
                    "category_remote_id": product_context["category_remote_id"],
                    "product_type_remote_id": getattr(product_context["product_type"], "remote_id", "") or "",
                }
            )
            payloads.append(row)

        return payloads

    def _build_product_context(
        self,
        *,
        product,
        translation,
        product_properties: list[ProductProperty],
        prices: list[dict[str, Any]],
        images: list[dict[str, Any]],
        ean: str,
        parent_sku: str,
        variant_group_code: str,
    ) -> dict[str, Any]:
        category_remote_id = self._resolve_category_remote_id(product=product)
        category = self._get_category_by_remote_id(remote_id=category_remote_id)
        product_type = self._get_product_type_by_remote_id(remote_id=category_remote_id)
        if product_type is None:
            raise ValidationError(
                f"Mirakl product type is missing for category '{category_remote_id or '-'}' on product {getattr(product, 'sku', product.id)}."
            )
        if not product_type.ready_to_push:
            raise ValidationError(
                f"Upload a template CSV to {product_type} in order to push product {getattr(product, 'sku', product.id)}."
            )

        property_by_id = {item.property_id: item for item in product_properties}
        remote_select_lookup = {
            (value.remote_property_id, value.local_instance_id): value
            for value in MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property__sales_channel=self.sales_channel,
                remote_property__local_instance_id__in=list(property_by_id.keys()),
                local_instance__isnull=False,
            ).select_related("remote_property", "local_instance")
        }

        return {
            "product": product,
            "translation": translation,
            "category_remote_id": category_remote_id,
            "category": category,
            "product_type": product_type,
            "product_properties": product_properties,
            "property_by_id": property_by_id,
            "prices": prices,
            "images": images,
            "ean": ean,
            "sku": getattr(product, "sku", "") or "",
            "parent_sku": parent_sku if product.id != self.local_product.id else "",
            "variant_group_code": variant_group_code if product.id != self.local_product.id else "",
            "name": getattr(translation, "name", None) or getattr(product, "name", ""),
            "short_description": getattr(translation, "short_description", None) or "",
            "description": getattr(translation, "description", None) or "",
            "url_key": getattr(translation, "url_key", None) or "",
            "remote_select_lookup": remote_select_lookup,
            "swatch_url": self._resolve_swatch_url(images=images, product_properties=product_properties),
        }

    def _build_header_row(self, *, product_context: dict[str, Any], header_properties: list[MiraklProperty]) -> dict[str, Any]:
        row: dict[str, Any] = {}
        missing_errors: list[str] = []
        bullet_indexes = self._build_representation_indexes(
            header_properties=header_properties,
            representation_type=MiraklProperty.REPRESENTATION_PRODUCT_BULLET_POINT,
        )
        image_indexes = self._build_representation_indexes(
            header_properties=header_properties,
            representation_type=MiraklProperty.REPRESENTATION_IMAGE,
        )
        product_context["_has_thumbnail_header"] = any(
            item.representation_type == MiraklProperty.REPRESENTATION_THUMBNAIL_IMAGE
            for item in header_properties
        )
        product_context["_has_swatch_header"] = any(
            item.representation_type == MiraklProperty.REPRESENTATION_SWATCH_IMAGE
            for item in header_properties
        )

        for remote_property in header_properties:
            try:
                resolved_value = self._resolve_property_value(
                    remote_property=remote_property,
                    product_context=product_context,
                    bullet_index=bullet_indexes.get(remote_property.id),
                    image_index=image_indexes.get(remote_property.id),
                )
            except ValidationError as exc:
                missing_errors.append(str(exc))
                continue
            row[remote_property.code] = resolved_value

        if missing_errors:
            raise ValidationError(missing_errors)

        return row

    def _resolve_property_value(
        self,
        *,
        remote_property: MiraklProperty,
        product_context: dict[str, Any],
        bullet_index: int | None = None,
        image_index: int | None = None,
    ) -> str:
        resolver_name = f"_resolve_{remote_property.representation_type}"
        resolver = getattr(self, resolver_name, None)
        if resolver is None:
            resolver = self._resolve_property
        value = resolver(
            remote_property=remote_property,
            product_context=product_context,
            bullet_index=bullet_index,
            image_index=image_index,
        )
        value = self._apply_remote_validations(remote_property=remote_property, value=value, product_context=product_context)
        if value in (None, "") and self._is_required_remote_property(remote_property=remote_property):
            raise ValidationError(
                f"Mirakl required field '{remote_property.code}' is missing for product {product_context['sku']}."
            )
        return self._stringify(value)

    def _resolve_property(
        self,
        *,
        remote_property: MiraklProperty,
        product_context: dict[str, Any],
        bullet_index: int | None = None,
        image_index: int | None = None,
    ) -> str:
        product_property = product_context["property_by_id"].get(remote_property.local_instance_id)
        if product_property is None:
            default_value = self._get_effective_default_value(remote_property=remote_property)
            if default_value:
                return default_value
            if remote_property.local_instance_id is None and not self._is_required_remote_property(remote_property=remote_property):
                return ""
            raise ValidationError(
                f"Map Mirakl field '{remote_property.code}' to a OneSila property or set a default value."
            )
        return self._serialize_property_value(
            product_property=product_property,
            remote_property=remote_property,
            remote_value_lookup=product_context["remote_select_lookup"],
        )

    def _resolve_unit(
        self,
        *,
        remote_property: MiraklProperty,
        product_context: dict[str, Any],
        bullet_index: int | None = None,
        image_index: int | None = None,
    ) -> str:
        return self._resolve_property(remote_property=remote_property, product_context=product_context)

    def _resolve_default_value(
        self,
        *,
        remote_property: MiraklProperty,
        product_context: dict[str, Any],
        bullet_index: int | None = None,
        image_index: int | None = None,
    ) -> str:
        return self._get_effective_default_value(remote_property=remote_property)

    def _resolve_product_title(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["name"]

    def _resolve_product_subtitle(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        translation = product_context["translation"]
        return getattr(translation, "subtitle", None) or ""

    def _resolve_product_description(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["description"]

    def _resolve_product_short_description(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["short_description"]

    def _resolve_product_bullet_point(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        bullet_points = self._split_bullet_points(
            product_context["short_description"],
            product_context["description"],
        )
        if bullet_index is not None:
            index = bullet_index
        else:
            index = self._extract_numeric_suffix(remote_property.code) - 1
        if index < 0:
            index = 0
        return bullet_points[index] if index < len(bullet_points) else ""

    def _resolve_product_sku(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["sku"]

    def _resolve_product_internal_id(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return str(product_context["product"].id)

    def _resolve_product_category(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["category_remote_id"]

    def _resolve_product_configurable_sku(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["parent_sku"] or product_context["sku"]

    def _resolve_product_configurable_id(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        parent_product = self.local_product if product_context["product"].id != self.local_product.id else product_context["product"]
        return str(getattr(parent_product, "id", "") or "")

    def _resolve_product_active(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._resolve_boolean_value(
            remote_property=remote_property,
            value=bool(getattr(product_context["product"], "active", False)),
        )

    def _resolve_product_url_key(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["url_key"]

    def _resolve_product_ean(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["ean"]

    def _resolve_thumbnail_image(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._get_main_image_url(images=product_context["images"])

    def _resolve_swatch_image(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return product_context["swatch_url"]

    def _resolve_image(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        code = remote_property.code or ""
        if code == "main_image":
            return self._get_main_image_url(images=product_context["images"])
        if image_index is None:
            additional_match = re.search(r"additional_(\d+)", code)
            image_index = int(additional_match.group(1)) - 1 if additional_match else 0
        return self._get_ranked_image_url(
            images=product_context["images"],
            index=image_index,
            has_thumbnail_header=bool(product_context.get("_has_thumbnail_header")),
            has_swatch_header=bool(product_context.get("_has_swatch_header")),
            swatch_url=product_context.get("swatch_url", ""),
        )

    def _resolve_video(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return ""

    def _resolve_document(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return ""

    def _resolve_price(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._stringify(self._get_primary_price(product_context["prices"]).get("price"))

    def _resolve_discounted_price(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._stringify(self._get_primary_price(product_context["prices"]).get("discount"))

    def _resolve_stock(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        if self.action != SalesChannelFeedItem.ACTION_CREATE:
            return ""
        starting_stock = getattr(self.sales_channel, "starting_stock", None)
        return "" if starting_stock is None else self._stringify(max(int(starting_stock), 0))

    def _resolve_vat_rate(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        vat_rate = getattr(product_context["product"], "vat_rate", None)
        rate = getattr(vat_rate, "rate", None)
        return "" if rate in (None, "") else self._stringify(rate)

    def _resolve_allow_backorder(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._resolve_boolean_value(
            remote_property=remote_property,
            value=bool(getattr(product_context["product"], "allow_backorder", False)),
        )

    def _resolve_condition(self, *, remote_property: MiraklProperty, product_context: dict[str, Any], bullet_index: int | None = None, image_index: int | None = None) -> str:
        return self._stringify((getattr(self.remote_product, "raw_data", {}) or {}).get("state_code", ""))

    def _get_header_properties(self, *, category: MiraklCategory | None, sales_channel_view) -> list[MiraklProperty]:
        if category is None:
            raise ValidationError("Mirakl product category is missing. Map the product to a Mirakl category or product type first.")
        return get_mirakl_category_header_properties(
            sales_channel=self.sales_channel,
            sales_channel_view=sales_channel_view,
            category_remote_id=category.remote_id,
        )

    def _resolve_category_remote_id(self, *, product) -> str:
        product_category = (
            MiraklProductCategory.objects.filter(product=product, sales_channel=self.sales_channel)
            .order_by("id")
            .first()
        )
        if product_category is not None and product_category.remote_id:
            return product_category.remote_id

        product_rule = product.get_product_rule(sales_channel=self.sales_channel)
        if product_rule is None:
            return ""

        product_type = MiraklProductType.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=product_rule,
        ).order_by("id").first()
        return getattr(product_type, "remote_id", "") or ""

    def _get_category_by_remote_id(self, *, remote_id: str) -> MiraklCategory | None:
        if remote_id not in self._category_cache:
            self._category_cache[remote_id] = (
                MiraklCategory.objects.select_related("parent").filter(
                    sales_channel=self.sales_channel,
                    remote_id=remote_id,
                ).first()
                if remote_id
                else None
            )
        return self._category_cache[remote_id]

    def _get_product_type_by_remote_id(self, *, remote_id: str) -> MiraklProductType | None:
        if remote_id not in self._product_type_cache:
            self._product_type_cache[remote_id] = (
                MiraklProductType.objects.select_related("category", "local_instance").filter(
                    sales_channel=self.sales_channel,
                    remote_id=remote_id,
                ).first()
                if remote_id
                else None
            )
        return self._product_type_cache[remote_id]

    def _serialize_property_value(
        self,
        *,
        product_property: ProductProperty,
        remote_property: MiraklProperty,
        remote_value_lookup: dict[tuple[int, int], MiraklPropertySelectValue],
    ) -> str:
        property_type = getattr(product_property.property, "type", "")
        if property_type == "SELECT" and product_property.value_select_id:
            mapped_value = remote_value_lookup.get((remote_property.id, product_property.value_select_id))
            if mapped_value is None:
                raise ValidationError(
                    f"Map the OneSila select value for Mirakl field '{remote_property.code}' before pushing."
                )
            return self._stringify(getattr(mapped_value, "value", None) or getattr(mapped_value, "code", None))
        if property_type == "MULTISELECT":
            values: list[str] = []
            for select_value in product_property.value_multi_select.all():
                mapped_value = remote_value_lookup.get((remote_property.id, select_value.id))
                if mapped_value is None:
                    raise ValidationError(
                        f"Map all OneSila multiselect values for Mirakl field '{remote_property.code}' before pushing."
                    )
                values.append(self._stringify(getattr(mapped_value, "value", None) or getattr(mapped_value, "code", None)))
            return ", ".join([value for value in values if value])
        return self._stringify(product_property.get_serialised_value(self.language))

    def _resolve_boolean_value(self, *, remote_property: MiraklProperty, value: bool) -> str:
        yes_text_value, no_text_value = self._get_effective_boolean_text_values(remote_property=remote_property)
        if remote_property.type == "BOOLEAN":
            if value and yes_text_value:
                return self._stringify(yes_text_value)
            if not value and no_text_value:
                return self._stringify(no_text_value)
            return "true" if value else "false"

        if remote_property.type == "SELECT":
            mapped_value = MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property=remote_property,
                bool_value=value,
            ).order_by("id").first()
            if mapped_value is not None:
                return self._stringify(mapped_value.value or mapped_value.code)

        return "true" if value else "false"

    def _apply_remote_validations(self, *, remote_property: MiraklProperty, value: Any, product_context: dict[str, Any]) -> Any:
        rendered = self._stringify(value)
        if rendered == "":
            return value

        validations = remote_property.validations
        validation_entries: list[str] = []
        if isinstance(validations, str):
            validation_entries = [validations]
        elif isinstance(validations, list):
            validation_entries = [str(entry) for entry in validations if entry not in (None, "")]

        for entry in validation_entries:
            parts = [part.strip() for part in str(entry).split("|") if part.strip()]
            if len(parts) != 2:
                continue
            rule, raw_limit = parts[0].upper(), parts[1]
            try:
                limit = int(raw_limit)
            except (TypeError, ValueError):
                continue

            if rule == "MAX_LENGTH" and len(rendered) > limit:
                raise ValidationError(
                    f"Mirakl field '{remote_property.code}' exceeds max length {limit} for product {product_context['sku']}."
                )
            if rule == "MIN_LENGTH" and len(rendered) < limit:
                raise ValidationError(
                    f"Mirakl field '{remote_property.code}' is shorter than min length {limit} for product {product_context['sku']}."
                )

        return value

    def _build_representation_indexes(self, *, header_properties: list[MiraklProperty], representation_type: str) -> dict[int, int]:
        matches = [item for item in header_properties if item.representation_type == representation_type]
        return {item.id: index for index, item in enumerate(matches)}

    def _resolve_swatch_url(self, *, images: list[dict[str, Any]], product_properties: list[ProductProperty]) -> str:
        for image in images:
            if image.get("is_swatch"):
                return self._stringify(image.get("url"))

        for product_property in product_properties:
            prop = product_property.property
            if not getattr(prop, "has_image", False):
                continue
            select_value = getattr(product_property, "value_select", None)
            image = getattr(select_value, "image", None)
            if image and hasattr(image, "image_url"):
                return self._stringify(image.image_url())

        return ""

    def _get_main_image_url(self, *, images: list[dict[str, Any]]) -> str:
        for image in images:
            if image.get("is_main"):
                return self._stringify(image.get("url"))
        if images:
            return self._stringify(images[0].get("url"))
        return ""

    def _get_ranked_image_url(
        self,
        *,
        images: list[dict[str, Any]],
        index: int,
        has_thumbnail_header: bool,
        has_swatch_header: bool,
        swatch_url: str,
    ) -> str:
        main_image_url = self._get_main_image_url(images=images)
        candidate_urls: list[str] = []
        seen: set[str] = set()

        for image in images:
            url = self._stringify(image.get("url"))
            if not url or url in seen:
                continue
            if has_thumbnail_header and url == main_image_url:
                continue
            if has_swatch_header and swatch_url and url == swatch_url:
                continue
            seen.add(url)
            candidate_urls.append(url)

        if not candidate_urls and not has_thumbnail_header and main_image_url:
            return main_image_url
        return candidate_urls[index] if 0 <= index < len(candidate_urls) else ""

    def _get_primary_price(self, prices: list[dict[str, Any]]) -> dict[str, Any]:
        return prices[0] if prices else {}

    def _split_bullet_points(self, *values: str) -> list[str]:
        bullets: list[str] = []
        for value in values:
            for part in re.split(r"[\n\r]+|•", str(value or "")):
                part = part.strip()
                if part:
                    bullets.append(part)
        return bullets

    def _extract_numeric_suffix(self, value: str) -> int:
        match = re.search(r"(\d+)(?!.*\d)", str(value or ""))
        return int(match.group(1)) if match else 1

    def _is_required_remote_property(self, *, remote_property: MiraklProperty) -> bool:
        return bool(remote_property.required or str(remote_property.requirement_level or "").upper() == "REQUIRED")

    def _get_effective_default_value(self, *, remote_property: MiraklProperty) -> str:
        public_definition = self._get_public_definition(remote_property=remote_property)
        if public_definition is not None and public_definition.default_value:
            return public_definition.default_value
        return remote_property.default_value or ""

    def _get_effective_boolean_text_values(self, *, remote_property: MiraklProperty) -> tuple[str, str]:
        public_definition = self._get_public_definition(remote_property=remote_property)
        if public_definition is not None:
            return (
                public_definition.yes_text_value or remote_property.yes_text_value or "",
                public_definition.no_text_value or remote_property.no_text_value or "",
            )
        return remote_property.yes_text_value or "", remote_property.no_text_value or ""

    def _get_public_definition(self, *, remote_property: MiraklProperty) -> MiraklPublicDefinition | None:
        if not getattr(remote_property, "representation_type_decided", False):
            return None
        if remote_property.code not in self._public_definition_cache:
            self._public_definition_cache[remote_property.code] = (
                MiraklPublicDefinition.objects.filter(
                    hostname=self.sales_channel.hostname,
                    property_code=remote_property.code,
                )
                .order_by("id")
                .first()
            )
        return self._public_definition_cache[remote_property.code]

    def _stringify(self, value: Any) -> str:
        if value in (None, ""):
            return ""
        return str(value)


class MiraklProductCreatePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_CREATE


class MiraklProductUpdatePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_UPDATE


class MiraklProductDeletePayloadFactory(_BaseMiraklProductPayloadFactory):
    action = SalesChannelFeedItem.ACTION_DELETE
