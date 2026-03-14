from __future__ import annotations

import csv
import io
import re
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify

from media.models import Media, MediaProductThrough
from products.models import Product
from properties.models import ProductProperty
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklProductCategory,
    MiraklProductType,
    MiraklProductTypeItem,
    MiraklProperty,
    MiraklPropertySelectValue,
)


class MiraklProductFeedFileFactory:
    """Render Mirakl product feed items into the real template-style CSV shape."""

    BASE_PRODUCT_COLUMNS = [
        "product_category",
        "parent_product_id",
        "product_id",
        "ean",
        "collection",
        "product_title",
        "long_description",
        "details_and_care",
        "colour",
        "colourfacet",
        "fabrication_type",
        "gender",
        "main_image",
        "image_(additional_1)",
        "image_(additional_2)",
        "image_(additional_3)",
        "image_(additional_4)",
        "image_(additional_5)",
        "image_(additional_6)",
        "image_(additional_7)",
        "image_(additional_8)",
        "image_(additional_9)",
        "image_(additional_10)",
        "image_(additional_11)",
        "swatch",
        "returns",
        "ethics",
        "sustainability_detail",
        "preloved",
        "preloved_condition_rating",
        "country_of_origin",
        "hs_code",
        "item_length",
        "item_width",
        "item_height",
        "item_weight",
        "customisationgroup",
    ]
    OFFER_COLUMNS = [
        "sku",
        "product-id",
        "product-id-type",
        "description",
        "internal-description",
        "price",
        "price-additional-info",
        "quantity",
        "min-quantity-alert",
        "state",
        "available-start-date",
        "available-end-date",
        "logistic-class",
        "discount-price",
        "discount-start-date",
        "discount-end-date",
        "leadtime-to-ship",
        "update-delete",
    ]

    def __init__(self, *, feed) -> None:
        self.feed = feed
        self.sales_channel = feed.sales_channel
        self._product_context_cache: dict[tuple[int | None, int | None], dict] = {}
        self._category_cache: dict[str, MiraklCategory | None] = {}
        self._product_type_items_cache: dict[tuple[int, int | None], list[MiraklProductTypeItem]] = {}
        self._template_headers_cache: dict[int, list[str]] = {}

    def run(self) -> str:
        rendered_rows, template_headers = self._build_rendered_rows()
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=self._build_fieldnames(rendered_rows=rendered_rows, template_headers=template_headers),
            delimiter=",",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for rendered_row in rendered_rows:
            writer.writerow(rendered_row)

        filename = self._build_filename()
        content = buffer.getvalue()
        if self.feed.file:
            self.feed.file.delete(save=False)
        self.feed.file.save(filename, ContentFile(content), save=False)
        self.feed.last_synced_at = timezone.now()
        self.feed.save(update_fields=["file", "last_synced_at"])
        return filename

    def _build_filename(self) -> str:
        seller_name = getattr(self.feed.sales_channel, "name", None) or getattr(self.feed.sales_channel, "hostname", None) or "mirakl"
        seller_slug = slugify(seller_name) or f"channel-{self.feed.sales_channel_id}"
        return f"mirakl-{self.feed.stage}-feed-{self.feed.sales_channel_id}-{seller_slug}-{self.feed.id or 'new'}.csv"

    def _build_rendered_rows(self) -> tuple[list[dict[str, str]], list[str]]:
        rendered_rows: list[dict[str, str]] = []
        template_headers: list[str] | None = None
        queryset = self.feed.items.select_related(
            "remote_product",
            "remote_product__local_instance",
            "sales_channel_view",
        ).all()
        for item in queryset:
            offer_payloads = list(item.payload_data.get("offer") or [])
            for index, row in enumerate(item.payload_data.get("rows") or []):
                context = self._get_product_context(
                    row_product_id=row.get("local_product_id"),
                    fallback_product_id=item.remote_product.local_instance_id,
                    sales_channel_view_id=item.sales_channel_view_id,
                )
                row_template_headers = self._get_template_headers(context=context)
                if template_headers is None:
                    template_headers = row_template_headers
                elif row_template_headers != template_headers:
                    raise ValidationError(
                        "Mirakl feed contains multiple product types/templates. Split the feed by product type before push."
                    )

                offer_payload = offer_payloads[index] if index < len(offer_payloads) else {}
                rendered_rows.append(
                    self._build_rendered_row(
                        item=item,
                        row=row,
                        offer_payload=offer_payload,
                        context=context,
                        template_headers=row_template_headers,
                    )
                )
        return rendered_rows, (template_headers or [])

    def _build_fieldnames(self, *, rendered_rows: list[dict[str, str]], template_headers: list[str]) -> list[str]:
        if template_headers:
            return template_headers

        dynamic_columns: list[str] = []
        excluded_columns = set(self.BASE_PRODUCT_COLUMNS) | set(self.OFFER_COLUMNS)
        for row in rendered_rows:
            for column in row.keys():
                if column in excluded_columns or column in dynamic_columns:
                    continue
                dynamic_columns.append(column)
        return [*self.BASE_PRODUCT_COLUMNS, *sorted(dynamic_columns), *self.OFFER_COLUMNS]

    def _build_rendered_row(self, *, item, row: dict, offer_payload: dict, context: dict, template_headers: list[str]) -> dict[str, str]:
        product_row = {
            key: value
            for key, value in row.items()
            if not str(key).startswith("_") and key not in self.OFFER_COLUMNS
        }
        if not product_row:
            product_row = self._build_base_product_columns(row=row, context=context)
            product_row.update(self._build_schema_columns(context=context))

        product_row.update(self._build_offer_columns(row=row, offer_payload=offer_payload, context=context))
        if not template_headers:
            return product_row

        unexpected_columns = sorted(
            column
            for column, value in product_row.items()
            if column not in template_headers and value not in ("", None)
        )
        if unexpected_columns:
            raise ValidationError(
                f"Mirakl template for {context['product_type']} is missing columns: {', '.join(unexpected_columns)}"
            )

        return {header: product_row.get(header, "") for header in template_headers}

    def _build_base_product_columns(self, *, row: dict, context: dict) -> dict[str, str]:
        images = list(row.get("images") or [])
        main_image = next((image.get("url") for image in images if image.get("is_main")), "")
        if not main_image and images:
            main_image = images[0].get("url") or ""
        additional_images = [image.get("url") for image in images if image.get("url") and image.get("url") != main_image][:11]

        base_row = {
            "product_category": context["category_remote_id"],
            "parent_product_id": row.get("parent_sku") or "",
            "product_id": row.get("sku") or "",
            "ean": row.get("ean") or "",
            "collection": self._lookup_mapped_value(context=context, code="collection"),
            "product_title": row.get("name") or "",
            "long_description": row.get("description") or row.get("short_description") or "",
            "details_and_care": self._lookup_mapped_value(context=context, code="details_and_care"),
            "colour": self._lookup_mapped_value(context=context, code="colour"),
            "colourfacet": self._lookup_mapped_value(context=context, code="colourfacet"),
            "fabrication_type": self._lookup_mapped_value(context=context, code="fabrication_type"),
            "gender": self._lookup_mapped_value(context=context, code="gender"),
            "main_image": main_image,
            "swatch": context["swatch_url"],
            "returns": self._lookup_mapped_value(context=context, code="returns"),
            "ethics": self._lookup_mapped_value(context=context, code="ethics"),
            "sustainability_detail": self._lookup_mapped_value(context=context, code="sustainability_detail"),
            "preloved": self._lookup_mapped_value(context=context, code="preloved"),
            "preloved_condition_rating": self._lookup_mapped_value(context=context, code="preloved_condition_rating"),
            "country_of_origin": self._lookup_mapped_value(context=context, code="country_of_origin"),
            "hs_code": self._lookup_mapped_value(context=context, code="hs_code"),
            "item_length": self._lookup_mapped_value(context=context, code="item_length"),
            "item_width": self._lookup_mapped_value(context=context, code="item_width"),
            "item_height": self._lookup_mapped_value(context=context, code="item_height"),
            "item_weight": self._lookup_mapped_value(context=context, code="item_weight"),
            "customisationgroup": self._lookup_mapped_value(context=context, code="customisationgroup"),
        }
        for index in range(1, 12):
            key = f"image_(additional_{index})"
            base_row[key] = additional_images[index - 1] if index <= len(additional_images) else ""
        return base_row

    def _build_schema_columns(self, *, context: dict) -> dict[str, str]:
        if not context["category"]:
            return {}

        row: dict[str, str] = {}
        for item in self._get_category_items(
            category=context["category"],
            sales_channel_view_id=context.get("sales_channel_view_id"),
        ):
            property_code = item.remote_property.code
            if property_code in self.BASE_PRODUCT_COLUMNS or property_code in self.OFFER_COLUMNS:
                continue
            row[property_code] = self._resolve_remote_property_value(context=context, remote_property=item.remote_property)
        return row

    def _build_offer_columns(self, *, row: dict, offer_payload: dict, context: dict) -> dict[str, str]:
        discount = offer_payload.get("discount") or {}
        leadtime = offer_payload.get("leadtime_to_ship") or row.get("leadtime_to_ship") or self._lookup_mapped_value(context=context, code="leadtime_to_ship")
        logistic_class = offer_payload.get("logistic_class") or self._lookup_mapped_value(context=context, code="logistic_class")
        quantity = offer_payload.get("quantity")
        if quantity in (None, ""):
            quantity = row.get("stock") or self._lookup_mapped_value(context=context, code="quantity")

        return {
            "sku": offer_payload.get("shop_sku") or row.get("sku") or "",
            "product-id": offer_payload.get("product_id") or row.get("product_ean") or row.get("ean") or row.get("sku") or "",
            "product-id-type": offer_payload.get("product_id_type") or ("EAN" if row.get("ean") else "SHOP_SKU"),
            "description": offer_payload.get("description") or row.get("product_description") or row.get("description") or row.get("product_short_description") or row.get("short_description") or "",
            "internal-description": offer_payload.get("internal_description") or row.get("name") or row.get("sku") or "",
            "price": self._stringify(offer_payload.get("price") or row.get("price")),
            "price-additional-info": offer_payload.get("price_additional_info") or "Price including taxes",
            "quantity": self._stringify(quantity),
            "min-quantity-alert": self._lookup_mapped_value(context=context, code="min_quantity_alert"),
            "state": offer_payload.get("state_code") or row.get("condition") or self._lookup_mapped_value(context=context, code="state") or "11",
            "available-start-date": offer_payload.get("available_started") or "",
            "available-end-date": offer_payload.get("available_ended") or "",
            "logistic-class": self._stringify(logistic_class),
            "discount-price": self._stringify(discount.get("price") or row.get("discounted_price")),
            "discount-start-date": discount.get("start_date") or "",
            "discount-end-date": discount.get("end_date") or "",
            "leadtime-to-ship": self._stringify(leadtime),
            "update-delete": str(offer_payload.get("update_delete") or row.get("action") or "").upper(),
        }

    def _get_product_context(self, *, row_product_id, fallback_product_id, sales_channel_view_id) -> dict:
        product_id = row_product_id or fallback_product_id
        cache_key = (product_id, sales_channel_view_id)
        if not product_id:
            return self._empty_context()
        if cache_key not in self._product_context_cache:
            self._product_context_cache[cache_key] = self._build_product_context(
                product_id=product_id,
                fallback_product_id=fallback_product_id,
                sales_channel_view_id=sales_channel_view_id,
            )
        return self._product_context_cache[cache_key]

    def _build_product_context(self, *, product_id: int, fallback_product_id: int | None, sales_channel_view_id: int | None) -> dict:
        product_properties = list(
            ProductProperty.objects.filter(product_id=product_id)
            .select_related("property", "value_select__image")
            .prefetch_related("value_multi_select__image")
            .order_by("id")
        )
        property_ids = [item.property_id for item in product_properties]
        category_remote_id = self._resolve_category_remote_id(product_id=product_id, fallback_product_id=fallback_product_id)
        category = self._get_category_by_remote_id(remote_id=category_remote_id)
        product_type = self._get_product_type_by_remote_id(remote_id=category_remote_id)
        remote_properties = list(
            MiraklProperty.objects.filter(
                sales_channel=self.sales_channel,
                local_instance_id__in=property_ids,
            ).select_related("local_instance")
        )
        remote_select_values = list(
            MiraklPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                remote_property__in=remote_properties,
                local_instance__isnull=False,
            ).select_related("remote_property", "local_instance")
        )
        image_assignments = list(
            MediaProductThrough.objects.filter(product_id=product_id)
            .select_related("media", "sales_channel")
            .order_by("-is_main_image", "sort_order", "id")
        )

        return {
            "product_id": product_id,
            "sales_channel_view_id": sales_channel_view_id,
            "category": category,
            "category_remote_id": category_remote_id,
            "product_type": product_type,
            "product_properties": product_properties,
            "property_by_id": {item.property_id: item for item in product_properties},
            "property_by_normalized_code": self._build_property_code_index(product_properties=product_properties),
            "remote_properties": remote_properties,
            "remote_property_select_values": {
                (value.remote_property_id, value.local_instance_id): value
                for value in remote_select_values
            },
            "swatch_url": self._resolve_swatch_url(image_assignments=image_assignments, product_properties=product_properties),
        }

    def _empty_context(self) -> dict:
        return {
            "product_id": None,
            "sales_channel_view_id": None,
            "category": None,
            "category_remote_id": "",
            "product_properties": [],
            "property_by_id": {},
            "property_by_normalized_code": {},
            "remote_properties": [],
            "remote_property_select_values": {},
            "swatch_url": "",
        }

    def _build_property_code_index(self, *, product_properties: list[ProductProperty]) -> dict[str, ProductProperty]:
        indexed: dict[str, ProductProperty] = {}
        for product_property in product_properties:
            internal_name = self._normalise_code(getattr(product_property.property, "internal_name", "") or "")
            name = self._normalise_code(getattr(product_property.property, "name", "") or "")
            if internal_name:
                indexed[internal_name] = product_property
            if name and name not in indexed:
                indexed[name] = product_property
        return indexed

    def _resolve_category_remote_id(self, *, product_id: int, fallback_product_id: int | None) -> str:
        product_category = (
            MiraklProductCategory.objects.filter(product_id=product_id, sales_channel=self.sales_channel)
            .order_by("id")
            .first()
        )
        if product_category is None and fallback_product_id and fallback_product_id != product_id:
            product_category = (
                MiraklProductCategory.objects.filter(product_id=fallback_product_id, sales_channel=self.sales_channel)
                .order_by("id")
                .first()
            )
        remote_id = getattr(product_category, "remote_id", "") or ""
        if remote_id:
            return remote_id

        product = Product.objects.filter(id=product_id).first()
        if product is None and fallback_product_id and fallback_product_id != product_id:
            product = Product.objects.filter(id=fallback_product_id).first()
        if product is None:
            return ""

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
                MiraklCategory.objects.filter(sales_channel=self.sales_channel, remote_id=remote_id).first()
                if remote_id
                else None
            )
        return self._category_cache[remote_id]

    def _get_product_type_by_remote_id(self, *, remote_id: str) -> MiraklProductType | None:
        if not remote_id:
            return None
        return (
            MiraklProductType.objects.filter(
                sales_channel=self.sales_channel,
                remote_id=remote_id,
            )
            .select_related("category", "local_instance")
            .first()
        )

    def _get_template_headers(self, *, context: dict) -> list[str]:
        product_type = context.get("product_type")
        if product_type is None or not product_type.ready_to_push:
            raise ValidationError(
                f"Upload a template CSV to Mirakl product type '{getattr(product_type, 'name', context.get('category_remote_id') or 'unknown')}' before pushing this product."
            )
        if product_type.id not in self._template_headers_cache:
            product_type.template.open("r")
            try:
                template_content = product_type.template.read()
                if isinstance(template_content, bytes):
                    template_content = template_content.decode("utf-8-sig")
                reader = csv.reader(io.StringIO(template_content))
                headers = [header.strip() for header in next(reader, []) if header.strip()]
                if not headers:
                    raise ValidationError(
                        f"Mirakl template for {product_type} is empty. Upload a CSV with a header row before pushing."
                    )
                self._template_headers_cache[product_type.id] = headers
            finally:
                product_type.template.close()
        return self._template_headers_cache[product_type.id]

    def _get_category_items(self, *, category: MiraklCategory, sales_channel_view_id: int | None) -> list[MiraklProductTypeItem]:
        product_type = self._get_product_type_by_remote_id(remote_id=category.remote_id)
        if product_type is None:
            return []
        cache_key = (product_type.id, sales_channel_view_id)
        if cache_key not in self._product_type_items_cache:
            items = list(
                MiraklProductTypeItem.objects.filter(product_type=product_type)
                .select_related("remote_property", "remote_property__local_instance")
                .prefetch_related("remote_property__applicabilities")
                .order_by("id")
            )
            self._product_type_items_cache[cache_key] = [
                item
                for item in items
                if self._is_item_applicable(
                    product_type_item=item,
                    sales_channel_view_id=sales_channel_view_id,
                )
            ]
        return self._product_type_items_cache[cache_key]

    def _is_item_applicable(self, *, product_type_item: MiraklProductTypeItem, sales_channel_view_id: int | None) -> bool:
        applicability_view_ids = [applicability.view_id for applicability in product_type_item.remote_property.applicabilities.all()]
        if not applicability_view_ids:
            return True
        if sales_channel_view_id is None:
            return False
        return sales_channel_view_id in applicability_view_ids

    def _lookup_mapped_value(self, *, context: dict, code: str) -> str:
        normalized = self._normalise_code(code)
        product_property = context["property_by_normalized_code"].get(normalized)
        if product_property:
            return self._serialize_local_value(product_property=product_property)
        return ""

    def _resolve_remote_property_value(self, *, context: dict, remote_property: MiraklProperty) -> str:
        product_property = context["property_by_id"].get(remote_property.local_instance_id)
        if not product_property:
            return remote_property.default_value or ""
        return self._serialize_property_value(
            product_property=product_property,
            remote_value_lookup=context["remote_property_select_values"],
            remote_object_id=remote_property.id,
        )

    def _serialize_property_value(self, *, product_property: ProductProperty, remote_value_lookup: dict, remote_object_id: int) -> str:
        property_type = getattr(product_property.property, "type", "")
        if property_type == "SELECT" and product_property.value_select_id:
            mapped_value = remote_value_lookup.get((remote_object_id, product_property.value_select_id))
            if mapped_value is not None:
                return self._stringify(getattr(mapped_value, "value", None) or getattr(mapped_value, "code", None))
        if property_type == "MULTISELECT":
            values: list[str] = []
            for select_value in product_property.value_multi_select.all():
                mapped_value = remote_value_lookup.get((remote_object_id, select_value.id))
                values.append(
                    self._stringify(
                        getattr(mapped_value, "value", None)
                        or getattr(mapped_value, "code", None)
                        or select_value.value
                    )
                )
            return ", ".join([value for value in values if value])
        if property_type == "BOOLEAN":
            value = product_property.get_value()
            return "Yes" if value else "No"
        return self._serialize_local_value(product_property=product_property)

    def _serialize_local_value(self, *, product_property: ProductProperty) -> str:
        value = product_property.get_serialised_value()
        if isinstance(value, list):
            return ", ".join([self._stringify(item) for item in value if item not in (None, "")])
        return self._stringify(value)

    def _resolve_swatch_url(self, *, image_assignments: list[MediaProductThrough], product_properties: list[ProductProperty]) -> str:
        for assignment in image_assignments:
            media = assignment.media
            if media.type == Media.IMAGE and media.image_type == Media.COLOR_SHOT:
                return media.image_url() or ""

        for product_property in product_properties:
            prop = product_property.property
            if not getattr(prop, "has_image", False):
                continue
            select_value = getattr(product_property, "value_select", None)
            image = getattr(select_value, "image", None)
            if image and hasattr(image, "image_url"):
                return image.image_url() or ""

        return ""

    def _normalise_code(self, value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
        return normalized

    def _stringify(self, value) -> str:
        if value in (None, ""):
            return ""
        return str(value)
