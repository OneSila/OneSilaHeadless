from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
import json
import logging
import pprint
from typing import Any, Dict, List, Tuple, Optional

from django.db.models import Q
from django.template import TemplateSyntaxError

from currencies.models import Currency
from media.models import Media, MediaProductThrough
from products.models import ProductTranslation
from properties.models import ProductProperty, Property
from sales_channels.integrations.ebay.factories.mixins import GetEbayAPIMixin
from sales_channels.factories.mixins import PreFlightCheckError
from sales_channels.models.sales_channels import SalesChannelViewAssign
from sales_channels.content_templates import (
    build_content_template_context,
    get_sales_channel_content_template,
    get_sales_channel_content_template_iframe,
    render_sales_channel_content_template,
)

from sales_channels.integrations.ebay.models.products import (
    EbayMediaThroughProduct,
    EbayProductOffer,
)
from sales_channels.integrations.ebay.models.properties import (
    EbayInternalProperty,
    EbayProductProperty,
    EbayProperty,
    EbayPropertySelectValue,
    EbayProductType,
)
from ebay_rest.api.sell_inventory.rest import ApiException
from ebay_rest.error import Error as EbayApiError

from sales_channels.integrations.ebay.exceptions import EbayResponseException
from sales_channels.integrations.ebay.models.taxes import EbayCurrency


logger = logging.getLogger(__name__)


def _extract_ebay_api_error_message(*, exc: Exception) -> str:
    """Return a human readable error message from an eBay API exception."""

    def _load_json(value: Any) -> Dict[str, Any] | None:
        if not value:
            return None
        if isinstance(value, bytes):
            try:
                value = value.decode("utf-8", errors="ignore")
            except Exception:
                return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return None
        if isinstance(value, dict):
            return value
        return None

    # ebay_rest.error.Error exposes as_dict with useful metadata
    as_dict = getattr(exc, "as_dict", None)
    if callable(as_dict):
        data = as_dict() or {}
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message") or error.get("detail")
            if message:
                return str(message)
        detail = data.get("detail")
        payload = _load_json(detail)
        if payload:
            errors = payload.get("errors")
            if isinstance(errors, list) and errors:
                messages = [err.get("message") for err in errors if isinstance(err, dict) and err.get("message")]
                if messages:
                    return "; ".join(messages)

    detail = getattr(exc, "detail", None)
    body = None
    if detail is not None:
        body = getattr(detail, "body", None) or getattr(detail, "response_body", None)

    payload = _load_json(body)
    if payload is None:
        # Attempt to parse JSON substring from str(exc)
        text = str(exc)
        start = text.find("{")
        if start != -1:
            payload = _load_json(text[start:])

    if isinstance(payload, dict):
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            messages = [err.get("message") for err in errors if isinstance(err, dict) and err.get("message")]
            if messages:
                return "; ".join(messages)
        message = payload.get("message")
        if message:
            return str(message)

    reason = getattr(exc, "reason", None)
    if reason:
        return str(reason)

    return str(exc)


class EbayInventoryItemPayloadMixin(GetEbayAPIMixin):
    """Utilities for building full eBay inventory item payloads."""

    remote_model_class = EbayMediaThroughProduct
    remote_eancode_update_factory = None
    _IDENTIFIER_FIELD_SHAPES: Dict[str, bool] = {
        "ean": True,
        "isbn": True,
        "upc": True,
        "epid": False,
        "mpn": False,
    }

    def __init__(self, *args: Any, get_value_only: bool = False, **kwargs: Any) -> None:
        if not hasattr(self, "view") or self.view is None:
            raise ValueError("Ebay factories require a marketplace view instance")

        if not hasattr(self, "get_value_only"):
            self.get_value_only = get_value_only
        self._latest_listing_description: str | None = None
        self._listing_policies_cache: Dict[str, Any] | None = None
        self._internal_property_options_cache: Dict[int, List[Any]] = {}
        self._content_template_cache: Dict[str, Any] = {}
        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def build_inventory_payload(self) -> Dict[str, Any]:
        """Return the full payload expected by eBay inventory item endpoints."""

        product = getattr(self.remote_product, "local_instance", None)
        if product is None:
            raise ValueError("Remote product missing local instance for payload build")

        language_code = self._get_language_code()
        translation = self._get_translation(language_code=language_code)
        title, subtitle, description, listing_description = self._extract_content(
            translation=translation,
            language_code=language_code,
        )

        aspects = self._build_aspects(language_code=language_code)
        internal_roots: Dict[str, Any] = {}
        product_section: Dict[str, Any] = {}
        self._apply_internal_properties(
            product_section=product_section,
            root_section=internal_roots,
            language_code=language_code,
        )

        image_urls = self._collect_image_urls(product=product)

        if image_urls:
            product_section["image_urls"] = image_urls

        ean_value = self._get_ean_value()
        normalized_ean = self._apply_identifier_shape(code="ean", value=ean_value)
        if normalized_ean:
            product_section["ean"] = normalized_ean

        if title:
            product_section["title"] = title[:80]
        if subtitle:
            product_section["subtitle"] = subtitle[:80]
        if description:
            product_section["description"] = description
        if language_code:
            product_section["locale"] = self._get_content_language()
        if aspects:
            product_section["aspects"] = aspects

        payload: Dict[str, Any] = {
            "sku": self._get_sku(product=product),
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": self._get_quantity(),
                }
            },
        }

        if product_section:
            payload["product"] = product_section

        if internal_roots:
            payload.update(internal_roots)

        self._latest_listing_description = listing_description or description
        return payload

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def _log_api_payload(self, *, action: str, payload: Any) -> None:
        try:
            serialized = json.dumps(payload, default=str, sort_keys=True, indent=2)
        except TypeError:
            serialized = pprint.pformat(payload)
        logger.info("eBay API %s payload:\n%s", action, serialized)

    # ------------------------------------------------------------------
    # Configurable helpers
    # ------------------------------------------------------------------
    def is_configurable_parent(self) -> bool:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None:
            return False
        is_configurable = getattr(product, "is_configurable", None)
        if callable(is_configurable):
            return bool(is_configurable())
        return False

    def get_parent_remote_sku(self) -> str:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None:
            return self.remote_product.remote_sku
        return product.sku

    def get_child_remote_skus(self) -> List[str]:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None or not self.is_configurable_parent():
            return []

        child_qs = getattr(product, "children", None)
        if callable(child_qs):  # configurable product proxy
            child_products = list(child_qs())
        else:
            try:
                from products.models import ConfigurableVariation

                child_products = list(
                    ConfigurableVariation.objects.filter(parent=product)
                    .select_related("variation")
                    .values_list("variation__sku", flat=True)
                )
            except Exception:  # pragma: no cover - fallback if relation missing
                child_products = []

        if not child_products:
            return []

        return [sku for sku in child_products if sku]

    def _get_configurable_child_products(self, *, product) -> List[Any]:
        if product is None or not self.is_configurable_parent():
            return []

        try:
            from products.models import ConfigurableVariation
        except ImportError:  # pragma: no cover
            return []

        child_products: List[Any] = []
        for mapping in ConfigurableVariation.objects.filter(parent=product).select_related("variation"):
            variation = getattr(mapping, "variation", None)
            if variation is not None:
                child_products.append(variation)

        return child_products

    def _build_inventory_group_payload(self) -> Dict[str, Any]:
        base_payload = self.build_inventory_payload()
        product_section = base_payload.get("product", {})
        product = getattr(self.remote_product, "local_instance", None)

        variant_skus = self.get_child_remote_skus()
        child_products = self._get_configurable_child_products(product=product)
        variation_aspects = (
            self._collect_variation_aspect_values(
                product=product,
                child_products=child_products,
            )
            if product
            else {}
        )
        varies_by = self._build_varies_by_configuration(product=product)
        common_child_aspects = self._collect_common_child_aspects(
            child_products=child_products,
            language_code=self._get_language_code(),
        )

        group_payload: Dict[str, Any] = {
            "description": product_section.get("description"),
            "imageUrls": product_section.get("image_urls", []),
            "inventoryItemGroupKey": self.get_parent_remote_sku(),
            "subtitle": product_section.get("subtitle"),
            "title": product_section.get("title"),
            "variantSKUs": variant_skus,
        }

        combined_aspects: Dict[str, List[str]] = {}

        parent_aspects = product_section.get("aspects")
        if isinstance(parent_aspects, Mapping):
            for name, value in parent_aspects.items():
                if isinstance(value, list):
                    cleaned = [str(entry) for entry in value if entry not in (None, "")]
                    if cleaned:
                        combined_aspects[name] = cleaned
                elif value not in (None, ""):
                    combined_aspects[name] = [str(value)]

        for name, values in common_child_aspects.items():
            combined_aspects[name] = values

        for name, values in variation_aspects.items():
            if len(values) == 1 and name not in combined_aspects:
                combined_aspects[name] = [next(iter(sorted(values)))]

        if combined_aspects:
            group_payload["aspects"] = combined_aspects

        if varies_by:
            group_payload["variesBy"] = varies_by

        return group_payload

    def _build_varies_by_configuration(self, *, product) -> Dict[str, Any] | None:
        if product is None:
            return None

        variation_data = self._collect_variation_dimensions(product=product)
        if not variation_data:
            return None

        aspects = sorted({name for name, _ in variation_data})
        specs: List[Dict[str, Any]] = []
        for name in aspects:
            values = sorted({value for aspect, value in variation_data if aspect == name})
            if values:
                specs.append({"name": name, "values": values})

        if not specs:
            return None

        return {
            "aspectsImageVariesBy": aspects,
            "specifications": specs,
        }

    def _format_variation_value(
        self,
        *,
        property_obj: Property,
        product_property: ProductProperty,
        language_code: str | None,
    ) -> str | None:
        if property_obj.type == Property.TYPES.SELECT:
            select_value = getattr(product_property, "value_select", None)
            if select_value is None:
                return None
            if language_code:
                translated = select_value.value_by_language_code(language=language_code)
                if translated not in (None, ""):
                    return str(translated)
            return str(select_value.value or "") or None

        if property_obj.type == Property.TYPES.MULTISELECT:
            values: list[str] = []
            for select_value in product_property.value_multi_select.all():
                if language_code:
                    translated = select_value.value_by_language_code(language=language_code)
                    if translated not in (None, ""):
                        values.append(str(translated))
                        continue
                raw_value = select_value.value
                if raw_value not in (None, ""):
                    values.append(str(raw_value))
            if not values:
                return None
            return ", ".join(sorted(values))

        raw_value = product_property.get_value()
        if isinstance(raw_value, str):
            raw_value = raw_value.strip()
        return str(raw_value) if raw_value not in (None, "") else None

    def _collect_variation_aspect_values(
        self,
        *,
        product,
        child_products: Sequence[Any] | None = None,
    ) -> Dict[str, set[str]]:
        if child_products is None:
            child_products = self._get_configurable_child_products(product=product)

        if not child_products:
            return {}

        variation_properties = list(
            product.get_configurator_properties()
            if hasattr(product, "get_configurator_properties")
            else []
        )

        if not variation_properties:
            return {}

        language_code = self._get_language_code()
        collected_values: dict[str, set[str]] = {}
        remote_property_map = self._get_remote_property_map()

        for variation in child_products:
            for rule_item in variation_properties:
                property_obj = getattr(rule_item, "property", None) or rule_item
                product_property = ProductProperty.objects.filter(
                    product=variation,
                    property=property_obj,
                ).select_related("property", "value_select").first()

                if product_property is None:
                    continue

                remote_property = remote_property_map.get(property_obj.id)
                if remote_property is None:
                    continue

                formatted_value = self._format_variation_value(
                    property_obj=property_obj,
                    product_property=product_property,
                    language_code=language_code,
                )
                if formatted_value in (None, ""):
                    continue

                aspect_name = (
                    remote_property.localized_name
                    or remote_property.translated_name
                    or remote_property.remote_id
                )
                if not aspect_name:
                    continue

                collected_values.setdefault(aspect_name, set()).add(formatted_value)

        return collected_values

    def _collect_variation_dimensions(self, *, product) -> List[Tuple[str, str]]:
        child_products = self._get_configurable_child_products(product=product)
        collected_values = self._collect_variation_aspect_values(
            product=product,
            child_products=child_products,
        )

        if not collected_values:
            return []

        collected: list[tuple[str, str]] = []
        for aspect_name, values in collected_values.items():
            if len(values) <= 1:
                continue
            for value in sorted(values):
                collected.append((aspect_name, value))

        return collected

    def _collect_common_child_aspects(
        self,
        *,
        child_products: Sequence[Any],
        language_code: str | None,
    ) -> Dict[str, List[str]]:
        if not child_products:
            return {}

        common_values: Dict[str, Tuple[str, ...]] | None = None

        for variation in child_products:
            child_aspect_map = self._compute_product_aspects(
                product=variation,
                language_code=language_code,
            )

            child_aspects: Dict[str, Tuple[str, ...]] = {
                name: tuple(sorted(value_list))
                for name, value_list in child_aspect_map.items()
                if value_list
            }

            if common_values is None:
                common_values = child_aspects
            else:
                common_values = {
                    name: values
                    for name, values in common_values.items()
                    if name in child_aspects and child_aspects[name] == values
                }

            if not common_values:
                break

        if not common_values:
            return {}

        result: Dict[str, List[str]] = {}
        for name, values in common_values.items():
            cleaned = [value for value in values if value not in (None, "")]
            if cleaned:
                result[name] = cleaned

        return result

    def get_listing_description(self) -> str | None:
        """Expose the last computed listing description for offer updates."""

        return self._latest_listing_description

    def serialize_response(self, response: Any) -> Any:  # pragma: no cover - thin wrapper
        return True if response is None else response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_language_code(self) -> str | None:
        remote_languages = getattr(self.view, "remote_languages", None)
        if remote_languages is not None:
            remote_language = remote_languages.first()
            if remote_language and remote_language.local_instance:
                return remote_language.local_instance

        return getattr(self.sales_channel.multi_tenant_company, "language", None)

    def _get_translation(self, *, language_code: str | None) -> ProductTranslation | None:
        product = self.remote_product.local_instance
        if language_code is None:
            return ProductTranslation.objects.filter(
                product=product,
                sales_channel=None,
            ).first()

        channel_translation = ProductTranslation.objects.filter(
            product=product,
            language=language_code,
            sales_channel=self.sales_channel,
        ).first()
        if channel_translation:
            return channel_translation

        return ProductTranslation.objects.filter(
            product=product,
            language=language_code,
            sales_channel=None,
        ).first()

    def _extract_content(
        self,
        *,
        translation: ProductTranslation | None,
        language_code: str | None,
    ) -> tuple[str | None, str | None, str | None, str | None]:
        product = self.remote_product.local_instance
        default_translation = None
        if translation and translation.sales_channel_id:
            default_translation = ProductTranslation.objects.filter(
                product=product,
                language=translation.language,
                sales_channel=None,
            ).first()
        elif translation:
            default_translation = translation

        title = None
        subtitle = None
        description = None
        listing_description = None

        if translation:
            title = translation.name or None
            subtitle = translation.subtitle or None
            description = translation.description or translation.short_description or None
            listing_description = translation.short_description or translation.description or None

        if not title and default_translation:
            title = default_translation.name or None
        if not subtitle and default_translation:
            subtitle = default_translation.subtitle or None
        if not description and default_translation:
            description = default_translation.description or default_translation.short_description or None
        if not listing_description and default_translation:
            listing_description = (
                default_translation.short_description
                or default_translation.description
                or None
            )

        if not title:
            title = getattr(product, "name", None)
        if not description:
            description = getattr(product, "description", None)

        template_language = language_code or (translation.language if translation else None)
        template_source = description or listing_description or getattr(product, "description", None)
        rendered_description, template_used = self._render_content_template(
            description=template_source,
            language=template_language,
            title=title or getattr(product, "name", None),
        )

        if template_used:
            resolved_description = rendered_description or template_source
            description = resolved_description
            listing_description = resolved_description

        return title, subtitle, description, listing_description

    def _get_content_template(self, *, language: str | None):
        if not language:
            return None

        if language in self._content_template_cache:
            return self._content_template_cache[language]

        template = get_sales_channel_content_template(
            sales_channel=self.sales_channel,
            language=language,
        )
        self._content_template_cache[language] = template
        return template

    def _render_content_template(
        self,
        *,
        description: str | None,
        language: str | None,
        title: str | None,
    ) -> Tuple[str | None, bool]:
        template = self._get_content_template(language=language)
        if template is None:
            return description, False

        template_string = getattr(template, "template", "") or ""
        if not template_string.strip():
            return description, False

        language_value = language or ""
        title_value = title or getattr(self.remote_product.local_instance, "name", "") or ""
        fallback_description = description

        try:
            context = build_content_template_context(
                product=self.remote_product.local_instance,
                sales_channel=self.sales_channel,
                description=fallback_description,
                language=language_value,
                title=title_value,
            )
            iframe_markup = get_sales_channel_content_template_iframe(
                template=template,
                product=self.remote_product.local_instance,
            )
            if iframe_markup:
                context["iframe"] = iframe_markup
            rendered = render_sales_channel_content_template(
                template_string=template_string,
                context=context,
            )
        except TemplateSyntaxError as exc:
            logger.warning(
                "Failed to render content template for %s (%s): %s",
                self.remote_product.local_instance,
                language_value or "default",
                exc,
            )
            return description, False

        return (rendered or fallback_description), True

    def _collect_image_urls(self, *, product) -> List[str]:
        throughs = (
            MediaProductThrough.objects.get_product_images(
                product=product,
                sales_channel=self.sales_channel,
            )
            .filter(media__type=Media.IMAGE)
            .order_by("sort_order")
        )

        urls: List[str] = []
        for through in throughs:
            media = through.media
            if media and media.image_web_url:
                urls.append(media.image_web_url)
        return urls

    def _collect_identifier_entries(self, *, value: Any) -> List[str]:
        if value in (None, ""):
            return []

        if isinstance(value, str):
            candidates: Iterable[Any] = [value]
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            candidates = value
        else:
            candidates = [value]

        normalized: List[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            if candidate in (None, ""):
                continue
            candidate_str = str(candidate).strip()
            if not candidate_str or candidate_str in seen:
                continue
            seen.add(candidate_str)
            normalized.append(candidate_str)

        return normalized

    def _apply_identifier_shape(self, *, code: str, value: Any) -> Any:
        expects_list = self._IDENTIFIER_FIELD_SHAPES.get(code)
        if expects_list is None:
            return value

        entries = self._collect_identifier_entries(value=value)
        if expects_list:
            return entries

        if not entries:
            return None

        return entries[0]

    def _get_ean_value(self) -> str | None:
        if getattr(self, "_ean_factory_marker", False):
            value = getattr(self, "_ean_value", None)
            return value or None

        factory_class = getattr(self, "remote_eancode_update_factory", None)
        if factory_class is None or not getattr(self, "remote_product", None):
            return None

        remote_instance = factory_class.remote_model_class.objects.filter(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
        ).first()

        factory_kwargs: Dict[str, Any] = {
            "sales_channel": self.sales_channel,
            "local_instance": self.remote_product.local_instance,
            "remote_product": self.remote_product,
            "view": self.view,
            "get_value_only": True,
        }

        if remote_instance is not None:
            factory_kwargs["remote_instance"] = remote_instance

        factory = factory_class(**factory_kwargs)
        if factory.get_value_only and getattr(factory, "api", None) is None:
            sentinel = getattr(self, "api", None)
            factory.api = sentinel if sentinel is not None else object()

        value = factory.run()
        return value or None

    def _get_sku(self, *, product) -> str:
        if getattr(self.remote_product, "remote_sku", None):
            return self.remote_product.remote_sku
        return product.sku

    def _get_quantity(self) -> int:
        starting_stock = getattr(self.sales_channel, "starting_stock", None)
        if starting_stock is None:
            return 0

        product = getattr(self.remote_product, "local_instance", None)
        if product is not None:
            if not getattr(product, "active", True):
                return 0

            is_configurable = getattr(product, "is_configurable", None)
            if callable(is_configurable) and is_configurable():
                return 0

        return max(int(starting_stock), 0)

    def _build_aspects(self, *, language_code: str | None) -> Dict[str, List[str]]:
        product = self.remote_product.local_instance
        product = self.remote_product.local_instance
        return self._compute_product_aspects(product=product, language_code=language_code)

    def _apply_internal_properties(
        self,
        *,
        product_section: Dict[str, Any],
        root_section: Dict[str, Any],
        language_code: str | None,
    ) -> None:
        product = self.remote_product.local_instance
        product_properties = {
            prop.property_id: prop
            for prop in ProductProperty.objects.filter(product=product)
        }
        if not product_properties:
            return

        internal_properties = (
            EbayInternalProperty.objects.filter(sales_channel=self.sales_channel)
            .select_related("local_instance")
            .prefetch_related('options__local_instance')
        )

        for internal_property in internal_properties:
            local_property = internal_property.local_instance
            if not local_property:
                continue
            product_property = product_properties.get(local_property.id)
            if not product_property:
                continue

            value = self._render_basic_property_value(
                product_property=product_property,
                language_code=language_code,
            )
            value = self._normalize_internal_property_value(
                internal_property=internal_property,
                product_property=product_property,
                value=value,
            )
            if value in (None, "", []):
                continue

            target = root_section if internal_property.is_root else product_section
            self._assign_nested_value(container=target, path=internal_property.code, value=value)

        self._apply_package_unit_defaults(root_section=root_section)

    def _render_property_value(
        self,
        *,
        product_property: ProductProperty,
        remote_property: EbayProperty,
        language_code: str | None,
    ) -> Any:
        local_property = product_property.property
        if local_property.type == Property.TYPES.SELECT:
            select_value = product_property.value_select
            if select_value is None:
                return None
            remote_value = EbayPropertySelectValue.objects.filter(
                sales_channel=self.sales_channel,
                marketplace=remote_property.marketplace,
                ebay_property=remote_property,
                local_instance=select_value,
            ).first()
            if remote_value:
                return remote_value.localized_value or remote_value.translated_value or remote_value.remote_id

            return select_value.value_by_language_code(language=language_code)

        if local_property.type == Property.TYPES.MULTISELECT:
            values: List[str] = []
            for select_value in product_property.value_multi_select.all():
                remote_value = EbayPropertySelectValue.objects.filter(
                    sales_channel=self.sales_channel,
                    marketplace=remote_property.marketplace,
                    ebay_property=remote_property,
                    local_instance=select_value,
                ).first()
                if remote_value and (remote_value.localized_value or remote_value.translated_value):
                    values.append(remote_value.localized_value or remote_value.translated_value)
                else:
                    fallback_value = select_value.value_by_language_code(language=language_code)
                    if fallback_value not in (None, ""):
                        values.append(fallback_value)
            filtered = [value for value in values if value not in (None, "")]
            return filtered or None

        value = product_property.get_serialised_value(language=language_code)
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            filtered = [str(entry) for entry in value if entry not in (None, "")]
            return filtered or None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if value in (None, ""):
            return None
        return str(value)

    def _render_basic_property_value(
        self,
        *,
        product_property: ProductProperty,
        language_code: str | None,
    ) -> Any:
        property_type = product_property.property.type
        if property_type == Property.TYPES.SELECT:
            select_value = product_property.value_select
            if select_value is None:
                return None
            return select_value.value_by_language_code(language=language_code)
        if property_type == Property.TYPES.MULTISELECT:
            values = [value.value_by_language_code(language=language_code) for value in product_property.value_multi_select.all()]
            filtered = [value for value in values if value not in (None, "")]
            return filtered or None
        value = product_property.get_serialised_value(language=language_code)
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            filtered = [entry for entry in value if entry not in (None, "")]
            return filtered or None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value

    def _assign_nested_value(self, *, container: Dict[str, Any], path: str, value: Any) -> None:
        if not path:
            return
        parts = path.split("__")
        current = container
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value

    def _prepare_property_remote_value(self, *, product_property: ProductProperty, remote_property: EbayProperty | None) -> str:
        language_code = self._get_language_code()
        if remote_property is not None:
            value = self._render_property_value(
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )
        else:
            value = self._render_basic_property_value(
                product_property=product_property,
                language_code=language_code,
            )
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True)
        if value is None:
            return ""
        return str(value)

    def _get_internal_property_options(self, *, internal_property: EbayInternalProperty) -> List[Any]:
        cache_key = internal_property.pk
        if cache_key is None:
            return []
        if cache_key not in self._internal_property_options_cache:
            options = list(
                internal_property.options.filter(is_active=True).order_by('sort_order', 'label')
            )
            self._internal_property_options_cache[cache_key] = options
        return self._internal_property_options_cache[cache_key]

    def _match_internal_property_option(
        self,
        *,
        internal_property: EbayInternalProperty,
        options: List[Any],
        raw_value: str,
    ) -> Optional[str]:
        normalized = (raw_value or "").strip()
        if not normalized:
            return None

        normalized_lower = normalized.lower()
        for option in options:
            if option.value and normalized_lower == option.value.lower():
                return option.value
            if option.label and normalized_lower == option.label.lower():
                return option.value

        allowed = ", ".join(option.value for option in options)
        raise PreFlightCheckError(
            f"Invalid value '{normalized}' for internal property '{internal_property.name}'."
            f" Choose one of: {allowed}"
        )

    def _normalize_internal_property_value(
        self,
        *,
        internal_property: EbayInternalProperty,
        product_property: ProductProperty,
        value: Any,
    ) -> Any:
        if internal_property.type != Property.TYPES.SELECT:
            return self._apply_identifier_shape(code=internal_property.code, value=value)

        options = self._get_internal_property_options(internal_property=internal_property)
        if not options or value in (None, "", []):
            return self._apply_identifier_shape(code=internal_property.code, value=value)

        property_type = product_property.property.type

        if property_type == Property.TYPES.SELECT:
            local_select = getattr(product_property, "value_select", None)
            if local_select is not None:
                matched_option = next(
                    (opt for opt in options if opt.local_instance_id == local_select.id),
                    None,
                )
                if matched_option:
                    return self._apply_identifier_shape(code=internal_property.code, value=matched_option.value)

        if property_type == Property.TYPES.MULTISELECT:
            local_values = list(product_property.value_multi_select.all())
            if local_values:
                normalized_values: List[str] = []
                for local_value in local_values:
                    matched_option = next(
                        (opt for opt in options if opt.local_instance_id == local_value.id),
                        None,
                    )
                    if matched_option:
                        normalized_values.append(matched_option.value)
                    else:
                        normalized_values.append(
                            self._match_internal_property_option(
                                internal_property=internal_property,
                                options=options,
                                raw_value=local_value.value,
                            )
                        )
                return self._apply_identifier_shape(code=internal_property.code, value=normalized_values)

        if isinstance(value, str):
            matched = self._match_internal_property_option(
                internal_property=internal_property,
                options=options,
                raw_value=value,
            )
            return self._apply_identifier_shape(code=internal_property.code, value=matched)

        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
            normalized_values: List[str] = []
            for entry in value:
                matched = self._match_internal_property_option(
                    internal_property=internal_property,
                    options=options,
                    raw_value=str(entry) if entry is not None else "",
                )
                if matched:
                    normalized_values.append(matched)
            return self._apply_identifier_shape(code=internal_property.code, value=normalized_values)

        matched = self._match_internal_property_option(
            internal_property=internal_property,
            options=options,
            raw_value=str(value),
        )
        return self._apply_identifier_shape(code=internal_property.code, value=matched)

    def _extract_listing_details(self, payload: Any) -> tuple[Optional[str], Optional[str]]:
        if not isinstance(payload, Mapping):
            return None, None

        listing = payload.get("listing") if isinstance(payload, Mapping) else None
        if isinstance(listing, Mapping):
            listing_id = listing.get("listing_id") or listing.get("listingId")
            listing_status = listing.get("listing_status") or listing.get("listingStatus")
        else:
            listing_id = payload.get("listing_id") or payload.get("listingId")
            listing_status = payload.get("listing_status") or payload.get("listingStatus")

        listing_id_str = str(listing_id).strip() if listing_id else None
        listing_status_str = str(listing_status).strip() if listing_status else None
        return listing_id_str or None, listing_status_str or None

    def _update_offer_from_payload(
        self,
        *,
        offer: EbayProductOffer | None,
        payload: Any,
    ) -> None:
        if offer is None or not payload:
            return

        listing_id, listing_status = self._extract_listing_details(payload)

        fields: list[str] = []
        if listing_id and offer.listing_id != listing_id:
            offer.listing_id = listing_id
            fields.append("listing_id")

        if listing_status and offer.listing_status != listing_status:
            offer.listing_status = listing_status
            fields.append("listing_status")

        if fields:
            offer.save(update_fields=fields)

    def _apply_package_unit_defaults(self, *, root_section: Dict[str, Any]) -> None:
        package_section = root_section.get("packageWeightAndSize")
        if not isinstance(package_section, dict):
            return

        dimensions = package_section.get("dimensions")
        if isinstance(dimensions, dict) and not dimensions.get("unit"):
            dimensions["unit"] = self._get_dimensions_unit()

        weight_section = package_section.get("weight")
        if isinstance(weight_section, dict) and not weight_section.get("unit"):
            weight_section["unit"] = self._get_weight_unit()

    def _get_dimensions_unit(self) -> str:
        unit = getattr(self.view, "length_unit", None)
        if not unit:
            unit = getattr(self.sales_channel, "length_unit", None)
        return (unit or "CENTIMETER").upper()

    def _get_weight_unit(self) -> str:
        unit = getattr(self.view, "weight_unit", None)
        if not unit:
            unit = getattr(self.sales_channel, "weight_unit", None)
        return (unit or "KILOGRAM").upper()

    def _get_offer_record(
        self,
        *,
        remote_product: Any | None = None,
    ) -> EbayProductOffer | None:
        candidate = remote_product or getattr(self, "remote_product", None)
        if candidate is None or self.view is None:
            return None

        return (
            EbayProductOffer.objects.filter(
                remote_product=candidate,
                sales_channel_view=self.view,
            )
            .select_related("remote_product", "sales_channel_view")
            .first()
        )

    def _ensure_offer_record(
        self,
        *,
        remote_product: Any | None = None,
    ) -> EbayProductOffer | None:
        candidate = remote_product or getattr(self, "remote_product", None)
        if candidate is None or self.view is None:
            return None

        offer = self._get_offer_record(remote_product=candidate)
        if offer is not None:
            fields: list[str] = []
            if offer.sales_channel_id != self.sales_channel.id:
                offer.sales_channel = self.sales_channel
                fields.append("sales_channel")
            mt_company_id = getattr(offer, "multi_tenant_company_id", None)
            expected_company = getattr(self.sales_channel, "multi_tenant_company_id", None)
            if expected_company and mt_company_id != expected_company:
                offer.multi_tenant_company = self.sales_channel.multi_tenant_company
                fields.append("multi_tenant_company")
            if fields:
                offer.save(update_fields=fields)
            self._attach_remote_product_assigns(remote_product=candidate)
            return offer

        defaults = {
            "sales_channel": self.sales_channel,
            "multi_tenant_company": getattr(self.sales_channel, "multi_tenant_company", None),
        }
        offer, _ = EbayProductOffer.objects.get_or_create(
            multi_tenant_company=candidate.multi_tenant_company,
            remote_product=candidate,
            sales_channel_view=self.view,
            defaults=defaults,
        )

        # Ensure relational defaults persisted if created without save()
        fields: list[str] = []
        if offer.sales_channel_id != self.sales_channel.id:
            offer.sales_channel = self.sales_channel
            fields.append("sales_channel")
        expected_company = getattr(self.sales_channel, "multi_tenant_company_id", None)
        if expected_company and getattr(offer, "multi_tenant_company_id", None) != expected_company:
            offer.multi_tenant_company = self.sales_channel.multi_tenant_company
            fields.append("multi_tenant_company")
        if fields:
            offer.save(update_fields=fields)

        self._attach_remote_product_assigns(remote_product=candidate)
        return offer

    def _attach_remote_product_assigns(self, *, remote_product: Any) -> None:
        product = getattr(remote_product, "local_instance", None)
        if product is None or self.view is None:
            return

        assigns = SalesChannelViewAssign.objects.filter(
            product=product,
            sales_channel_view=self.view,
        )

        remote_product_id = getattr(remote_product, "id", None)

        for assign in assigns:
            fields: list[str] = []

            if assign.remote_product_id != remote_product_id:
                assign.remote_product = remote_product
                fields.append("remote_product")

            if assign.sales_channel_id != self.sales_channel.id:
                assign.sales_channel = self.sales_channel
                fields.append("sales_channel")

            if fields:
                assign.save(update_fields=fields)

    def _get_offer_remote_id(self) -> str | None:
        offer = self._get_offer_record()
        if offer and offer.remote_id:
            return str(offer.remote_id)

        remote_product = getattr(self, "remote_product", None)
        if (
            offer is None
            and remote_product is not None
            and getattr(remote_product, "is_variation", False)
            and getattr(remote_product, "remote_parent_product", None)
        ):
            parent_offer = self._get_offer_record(remote_product=remote_product.remote_parent_product)
            if parent_offer and parent_offer.remote_id:
                return str(parent_offer.remote_id)

        return None

    def _get_content_language(self) -> str:
        remote_languages = getattr(self.view, "remote_languages", None)
        if remote_languages is not None:
            remote_language = remote_languages.first()
            if remote_language and remote_language.remote_code:
                return remote_language.remote_code.replace("_", "-").lower()

        language_code = self._get_language_code()
        if language_code:
            return language_code.replace("_", "-").lower()
        return "en-us"

    def _compute_product_aspects(
        self,
        *,
        product,
        language_code: str | None,
    ) -> Dict[str, List[str]]:
        if product is None:
            return {}

        product_properties = {
            prop.property_id: prop
            for prop in ProductProperty.objects.filter(product=product)
        }

        if not product_properties:
            return {}

        aspects: Dict[str, List[str]] = {}
        property_map = self._get_remote_property_map()

        for property_id, product_property in product_properties.items():
            remote_property = property_map.get(property_id)
            if remote_property is None:
                continue

            values = self._render_property_value(
                product_property=product_property,
                remote_property=remote_property,
                language_code=language_code,
            )
            if not values:
                continue

            aspect_name = (
                remote_property.localized_name
                or remote_property.translated_name
                or remote_property.remote_id
            )

            if not aspect_name:
                continue

            if isinstance(values, str):
                values_list = [values]
            else:
                values_list = [str(value) for value in values if value not in (None, "")]

            if not values_list:
                continue

            aspects[aspect_name] = values_list

        return aspects

    def _get_remote_property_map(self) -> Dict[int, EbayProperty]:
        return {
            remote_property.local_instance_id: remote_property
            for remote_property in EbayProperty.objects.filter(sales_channel=self.sales_channel)
            .filter(Q(marketplace=self.view) | Q(marketplace__isnull=True))
            .select_related("local_instance")
            if getattr(remote_property, "local_instance_id", None) is not None
        }

    def _ensure_offer_for_remote(self, *, remote_product: Any) -> EbayProductOffer | None:
        return self._ensure_offer_record(remote_product=remote_product)

    def _update_remote_product_fields(
        self,
        *,
        remote_product: Any | None,
        fields: Sequence[str],
    ) -> None:
        if remote_product is None or not fields:
            return

        pk = getattr(remote_product, "pk", None)
        if pk is None:
            return

        update_kwargs = {field: getattr(remote_product, field) for field in fields}
        type(remote_product).objects.filter(pk=pk).update(**update_kwargs)
        for field, value in update_kwargs.items():
            setattr(remote_product, field, value)

    def _update_offer_fields(
        self,
        *,
        offer: EbayProductOffer | None,
        fields: Sequence[str],
    ) -> None:
        if offer is None or not fields:
            return

        offer.save(update_fields=list(fields))

    @contextmanager
    def _use_remote_product(self, remote_product: Any) -> Iterable[None]:
        original_remote_product = getattr(self, "remote_product", None)
        original_remote_instance = getattr(self, "remote_instance", None)
        try:
            self.remote_product = remote_product
            self.remote_instance = remote_product
            yield
        finally:
            self.remote_product = original_remote_product
            self.remote_instance = original_remote_instance

    def _get_primary_currency(self) -> Currency | None:
        view = getattr(self, "view", None)
        if view is None:
            return None

        remote_currency = (
            EbayCurrency.objects.filter(
                sales_channel=self.sales_channel,
                sales_channel_view=view,
            )
            .select_related("local_instance")
            .first()
        )

        view_label = getattr(view, "name", None) or getattr(view, "remote_id", None) or "the selected eBay marketplace"

        if remote_currency is None:
            raise PreFlightCheckError(
                f"No currency configured for {view_label}. Please map the marketplace currency before pushing products."
            )

        local_currency = getattr(remote_currency, "local_instance", None)
        if local_currency is None:
            code = getattr(remote_currency, "remote_code", None) or "the marketplace currency"
            raise PreFlightCheckError(
                f"{code} is not linked to a local currency for {view_label}. Please complete the currency mapping and retry."
            )

        return local_currency

    def _build_listing_policies(self) -> Dict[str, Any]:
        if self._listing_policies_cache is not None:
            return dict(self._listing_policies_cache)

        policies: Dict[str, Any] = {}
        fulfillment_id = getattr(self.view, "fulfillment_policy_id", None)
        payment_id = getattr(self.view, "payment_policy_id", None)
        return_id = getattr(self.view, "return_policy_id", None)

        missing: list[str] = []
        if fulfillment_id:
            policies["fulfillmentPolicyId"] = fulfillment_id
        else:
            missing.append("fulfillment policy")

        if payment_id:
            policies["paymentPolicyId"] = payment_id
        else:
            missing.append("payment policy")

        if return_id:
            policies["returnPolicyId"] = return_id
        else:
            missing.append("return policy")

        if missing:
            raise PreFlightCheckError(
                "Missing eBay listing policies ({}). Please configure the marketplace policies before pushing products.".format(
                    ", ".join(missing)
                )
            )

        self._listing_policies_cache = policies
        return dict(policies)

    def _get_category_id(self) -> str | None:
        category_id: str | None = None
        product = getattr(self.remote_product, "local_instance", None)
        view = getattr(self, "view", None)

        if product is not None and view is not None and hasattr(product, "get_product_rule"):
            try:
                rule = product.get_product_rule()
            except Exception:  # pragma: no cover - defensive guard
                rule = None

            if rule is not None:
                product_type = (
                    EbayProductType.objects.filter(
                        sales_channel=self.sales_channel,
                        marketplace=view,
                        local_instance=rule,
                    )
                    .exclude(remote_id__in=(None, ""))
                    .first()
                )
                if product_type and product_type.remote_id:
                    category_id = str(product_type.remote_id)

        return category_id if category_id not in (None, "") else None

    def _build_pricing_summary(self) -> Dict[str, Any]:
        product = getattr(self.remote_product, "local_instance", None)
        currency = self._get_primary_currency()

        if product is None or currency is None:
            return {}

        base_price, discount_price = product.get_price_for_sales_channel(
            self.sales_channel,
            currency=currency,
        )

        effective_price = discount_price if discount_price is not None else base_price
        if effective_price is None:
            currency_code = getattr(currency, "iso_code", None) or getattr(currency, "code", None) or "the marketplace currency"
            sku = getattr(product, "sku", None) or getattr(product, "id", "product")
            view_label = (
                getattr(self.view, "name", None)
                or getattr(self.view, "remote_id", None)
                or "the selected eBay marketplace"
            )
            raise EbayResponseException(
                f"No {currency_code} price found for SKU {sku} on {view_label}. Please configure a {currency_code} price and retry."
            )

        summary: Dict[str, Any] = {
            "price": {
                "currency": currency.iso_code,
                "value": float(effective_price),
            }
        }

        if (
            discount_price is not None
            and base_price is not None
            and float(discount_price) != float(base_price)
        ):
            summary["originalRetailPrice"] = {
                "currency": currency.iso_code,
                "value": float(base_price),
            }
            summary["originallySoldForRetailPriceOn"] = "OFF_EBAY"

        return summary

    def _build_tax_section(self) -> Dict[str, Any]:
        product = getattr(self.remote_product, "local_instance", None)
        vat_rate = getattr(product, "vat_rate", None)
        tax: Dict[str, Any] = {"applyTax": False}

        if vat_rate is None:
            return tax

        rate = getattr(vat_rate, "rate", None)
        if rate is None:
            tax["vatPercentage"] = None
            return tax

        tax["applyTax"] = True
        tax["vatPercentage"] = float(rate)
        return tax

    def _get_merchant_location_key(self) -> str | None:
        return getattr(self.view, "merchant_location_key", None)

    def _get_listing_duration(self) -> str:
        duration = getattr(self.view, "listing_duration", None)
        return duration or "GTC"

    def _build_offer_base_payload(self, *, product) -> Dict[str, Any]:
        return {
            "sku": self._get_sku(product=product),
            "marketplaceId": getattr(self.view, "remote_id", None),
            "format": "FIXED_PRICE",
            "listingDuration": self._get_listing_duration(),
        }

    def _build_offer_metadata(self) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}
        listing_description = self.get_listing_description()
        if listing_description:
            metadata["listingDescription"] = listing_description

        merchant_key = self._get_merchant_location_key()
        if merchant_key:
            metadata["merchantLocationKey"] = merchant_key

        return metadata

    def _apply_offer_section(self, *, payload: Dict[str, Any], key: str, value: Any) -> None:
        if isinstance(value, Mapping):
            if value:
                payload[key] = value
            return
        if value not in (None, ""):
            payload[key] = value

    def build_offer_payload(self) -> Dict[str, Any]:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None:
            raise ValueError("Remote product missing local instance for offer payload build")

        payload = self._build_offer_base_payload(product=product)

        metadata = self._build_offer_metadata()
        for key, value in metadata.items():
            self._apply_offer_section(payload=payload, key=key, value=value)

        self._apply_offer_section(
            payload=payload,
            key="categoryId",
            value=self._get_category_id(),
        )
        self._apply_offer_section(
            payload=payload,
            key="listingPolicies",
            value=self._build_listing_policies(),
        )
        self._apply_offer_section(
            payload=payload,
            key="pricingSummary",
            value=self._build_pricing_summary(),
        )
        self._apply_offer_section(
            payload=payload,
            key="tax",
            value=self._build_tax_section(),
        )

        return payload

    def _extract_offer_id(self, response: Any) -> str | None:
        if isinstance(response, dict):
            for key in ("offer_id", "offerId", "id"):
                candidate = response.get(key)
                if candidate:
                    return str(candidate)
        return None

    def _extract_offer_id_from_error(self, *, exc: Exception) -> str | None:
        payload: Any = None

        for attr in ("body", "response_body", "detail", "response_data"):
            payload = getattr(exc, attr, None)
            if payload:
                break

        if isinstance(payload, bytes):
            try:
                payload = payload.decode("utf-8", errors="ignore")
            except Exception:
                payload = None

        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (TypeError, ValueError):
                payload = None

        if not isinstance(payload, dict):
            as_dict = getattr(exc, "as_dict", None)
            if callable(as_dict):
                try:
                    payload = as_dict() or None
                except Exception:
                    payload = None

        if not isinstance(payload, dict):
            return None

        errors = payload.get("errors")
        if isinstance(errors, list):
            for error in errors:
                if not isinstance(error, dict):
                    continue
                parameters = error.get("parameters")
                if isinstance(parameters, list):
                    for param in parameters:
                        if not isinstance(param, dict):
                            continue
                        name = param.get("name")
                        if name and name.lower() == "offerid":
                            value = param.get("value")
                            if value:
                                return str(value)

        return None

    def send_offer(self) -> Any:
        payload = self.build_offer_payload()

        if self.get_value_only:
            return payload

        api = getattr(self, "api", None) or self.get_api()
        self.api = api

        offer_record = self._ensure_offer_record()
        offer_id = getattr(offer_record, "remote_id", None)

        def _update_offer(target_offer_id: str) -> Any:
            self._log_api_payload(action="update_offer", payload=payload)
            try:
                return api.sell_inventory_update_offer(
                    offer_id=target_offer_id,
                    body=payload,
                    content_language=self._get_content_language(),
                    content_type="application/json",
                )
            except (EbayApiError, ApiException) as exc:
                message = _extract_ebay_api_error_message(exc=exc)
                raise EbayResponseException(message) from exc

        if offer_id:
            response = _update_offer(offer_id)
        else:
            self._log_api_payload(action="create_offer", payload=payload)
            try:
                response = api.sell_inventory_create_offer(
                    body=payload,
                    content_language=self._get_content_language(),
                    content_type="application/json",
                )
            except (EbayApiError, ApiException) as exc:
                existing_offer_id = self._extract_offer_id_from_error(exc=exc)
                if existing_offer_id:
                    if offer_record and offer_record.remote_id != existing_offer_id:
                        offer_record.remote_id = existing_offer_id
                        self._update_offer_fields(offer=offer_record, fields=("remote_id",))
                    response = _update_offer(existing_offer_id)
                    offer_id = existing_offer_id
                else:
                    message = _extract_ebay_api_error_message(exc=exc)
                    raise EbayResponseException(message) from exc

        offer_record = offer_record or self._ensure_offer_record()
        response_offer_id = self._extract_offer_id(response)
        final_offer_id = response_offer_id or offer_id

        if offer_record:
            if final_offer_id and offer_record.remote_id != final_offer_id:
                offer_record.remote_id = final_offer_id
                self._update_offer_fields(offer=offer_record, fields=("remote_id",))
            self._update_offer_from_payload(offer=offer_record, payload=response)

        return response

    def publish_offer(self) -> Any:
        offer_id = self._get_offer_remote_id()
        if not offer_id:
            return {"offer_id": None} if self.get_value_only else None

        if self.get_value_only:
            return {"offer_id": offer_id}

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        try:
            response = api.sell_inventory_publish_offer(offer_id=offer_id)
        except (EbayApiError, ApiException) as exc:
            message = _extract_ebay_api_error_message(exc=exc)
            raise EbayResponseException(message) from exc

        offer_record = self._ensure_offer_record()
        if offer_record:
            self._update_offer_from_payload(offer=offer_record, payload=response)

        return response

    def withdraw_offer(self) -> Any:
        offer_id = self._get_offer_remote_id()
        if not offer_id:
            return {"offer_id": None} if self.get_value_only else None

        if self.get_value_only:
            return {"offer_id": offer_id}

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        try:
            response = api.sell_inventory_withdraw_offer(offer_id=offer_id)
        except (EbayApiError, ApiException) as exc:
            message = _extract_ebay_api_error_message(exc=exc)
            raise EbayResponseException(message) from exc

        offer_record = self._ensure_offer_record()
        if offer_record:
            fields: list[str] = []
            if offer_record.successfully_created:
                offer_record.successfully_created = False
                fields.append("successfully_created")
            if offer_record.listing_id:
                offer_record.listing_id = None
                fields.append("listing_id")
            if offer_record.listing_status:
                offer_record.listing_status = None
                fields.append("listing_status")
            if fields:
                self._update_offer_fields(offer=offer_record, fields=fields)

        return response

    def delete_inventory(self) -> Any:
        product = getattr(self.remote_product, "local_instance", None)
        if product is None:
            return None

        sku = self._get_sku(product=product)
        if self.get_value_only:
            return {"sku": sku}

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        try:
            response = api.sell_inventory_delete_inventory_item(sku=sku)
        except (EbayApiError, ApiException) as exc:
            message = _extract_ebay_api_error_message(exc=exc)
            raise EbayResponseException(message) from exc

        remote_product = getattr(self, "remote_product", None)
        if remote_product and getattr(remote_product, "remote_id", None):
            remote_product.remote_id = None
            self._update_remote_product_fields(
                remote_product=remote_product,
                fields=("remote_id",),
            )

        return response

    def delete_offer(self) -> Any:
        offer_id = self._get_offer_remote_id()
        if not offer_id:
            return {"offer_id": None} if self.get_value_only else None

        if self.get_value_only:
            return {"offer_id": offer_id}

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        try:
            response = api.sell_inventory_delete_offer(offer_id=offer_id)
        except (EbayApiError, ApiException) as exc:
            message = _extract_ebay_api_error_message(exc=exc)
            raise EbayResponseException(message) from exc

        offer_record = self._ensure_offer_record()
        if offer_record and offer_record.remote_id:
            offer_record.remote_id = None
            fields = ["remote_id"]
            if offer_record.listing_id:
                offer_record.listing_id = None
                fields.append("listing_id")
            if offer_record.listing_status:
                offer_record.listing_status = None
                fields.append("listing_status")
            if offer_record.successfully_created:
                offer_record.successfully_created = False
                fields.append("successfully_created")
            self._update_offer_fields(offer=offer_record, fields=fields)

        return response


class EbayInventoryItemPushMixin(EbayInventoryItemPayloadMixin):
    """Mixin adding API submission helpers for inventory payloads."""

    _BULK_MAX_BATCH = 25

    def __init__(self, *args: Any, view=None, get_value_only: bool = False, **kwargs: Any) -> None:
        if view is None:
            raise ValueError("Ebay factories require a marketplace view instance")

        self.view = view
        if "get_value_only" not in kwargs:
            kwargs["get_value_only"] = get_value_only
        self.get_value_only = kwargs["get_value_only"]
        super().__init__(*args, **kwargs)

    def send_inventory_payload(self) -> Any:
        is_parent = self.is_configurable_parent()
        if is_parent:
            payload = self._build_inventory_group_payload()
            action = "create_or_replace_inventory_item_group"
        else:
            payload = self.build_inventory_payload()
            action = "create_or_replace_inventory_item"

        if self.get_value_only:
            return payload

        api = getattr(self, "api", None) or self.get_api()
        self.api = api

        self._log_api_payload(action=action, payload=payload)

        try:
            if is_parent:
                return api.sell_inventory_create_or_replace_inventory_item_group(
                    body=payload,
                    content_language=self._get_content_language(),
                    content_type="application/json",
                    inventory_item_group_key=self.get_parent_remote_sku(),
                )

            sku = payload.get("sku")
            if not sku:
                product = getattr(self.remote_product, "local_instance", None)
                if product is not None:
                    sku = self._get_sku(product=product)

            return api.sell_inventory_create_or_replace_inventory_item(
                sku=sku,
                body=payload,
                content_language=self._get_content_language(),
                content_type="application/json",
            )
        except (EbayApiError, ApiException) as exc:
            message = _extract_ebay_api_error_message(exc=exc)
            raise EbayResponseException(message) from exc

    def _chunk_requests(self, requests: Sequence[Any]) -> List[List[Any]]:
        if not requests:
            return []
        return [
            list(requests[index : index + self._BULK_MAX_BATCH])
            for index in range(0, len(requests), self._BULK_MAX_BATCH)
        ]

    def build_bulk_inventory_requests(self, *, remote_products: Sequence[Any]) -> List[Dict[str, Any]]:
        requests: List[Dict[str, Any]] = []
        for remote_product in list(remote_products):
            with self._use_remote_product(remote_product):
                requests.append(self.build_inventory_payload())
        return requests

    def send_bulk_inventory_payloads(self, *, remote_products: Sequence[Any]) -> List[Any]:
        remote_products = list(remote_products)
        if self.get_value_only:
            requests = self.build_bulk_inventory_requests(remote_products=remote_products)
            batches = self._chunk_requests(requests)
            return [{"requests": batch} for batch in batches]

        if not remote_products:
            return []

        api = getattr(self, "api", None) or self.get_api()
        self.api = api

        responses: List[Any] = []
        for remote_product in remote_products:
            with self._use_remote_product(remote_product):
                responses.append(self.send_inventory_payload())

        return responses

    def build_bulk_offer_requests(self, *, remote_products: Sequence[Any]) -> List[Dict[str, Any]]:
        requests: List[Dict[str, Any]] = []
        for remote_product in list(remote_products):
            with self._use_remote_product(remote_product):
                requests.append({"offer": self.build_offer_payload()})
        return requests

    def _store_bulk_offer_ids(
        self,
        *,
        response: Any,
        remote_products: Sequence[Any],
    ) -> None:
        if not isinstance(response, Mapping):
            return

        entries = response.get("responses")
        if not isinstance(entries, Sequence):
            return

        for remote_product, entry in zip(remote_products, entries):
            offer = self._ensure_offer_record(remote_product=remote_product)
            if offer is None:
                continue

            offer_id = self._extract_offer_id(entry)
            if offer_id and offer.remote_id != offer_id:
                offer.remote_id = offer_id
                self._update_offer_fields(offer=offer, fields=("remote_id",))

            self._update_offer_from_payload(
                offer=offer,
                payload=entry if isinstance(entry, Mapping) else {},
            )

    def send_bulk_offer_payloads(self, *, remote_products: Sequence[Any]) -> List[Any]:

        # @TODO: Use the non bulk api until we figure it out why the bulk one always have errors
        remote_products = list(remote_products)
        if self.get_value_only:
            requests = self.build_bulk_offer_requests(remote_products=remote_products)
            batches = self._chunk_requests(requests)
            return [{"requests": batch} for batch in batches]

        if not remote_products:
            return []

        api = getattr(self, "api", None) or self.get_api()
        self.api = api

        responses: List[Any] = []
        for remote_product in remote_products:
            with self._use_remote_product(remote_product):
                responses.append(self.send_offer())

        return responses

    def _build_group_action_payload(self) -> Dict[str, Any]:
        return {
            "inventoryItemGroupKey": self.get_parent_remote_sku(),
            "marketplaceId": getattr(self.view, "remote_id", None),
        }

    def publish_group(self) -> Any:
        payload = self._build_group_action_payload()
        if self.get_value_only:
            return payload

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        self._log_api_payload(action="publish_inventory_item_group", payload=payload)
        try:
            response = api.sell_inventory_publish_offer_by_inventory_item_group(
                body=payload,
                content_type="application/json",
            )
        except (EbayApiError, ApiException) as exc:
            message = _extract_ebay_api_error_message(exc=exc)
            raise EbayResponseException(message) from exc

        offer_record = self._ensure_offer_record()
        if offer_record:
            self._update_offer_from_payload(offer=offer_record, payload=response)

        return response

    def withdraw_group(self) -> Any:
        payload = self._build_group_action_payload()
        if self.get_value_only:
            return payload

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        self._log_api_payload(action="withdraw_inventory_item_group", payload=payload)
        try:
            response = api.sell_inventory_withdraw_offer_by_inventory_item_group(
                body=payload,
                content_type="application/json",
            )
        except (EbayApiError, ApiException) as exc:
            message = _extract_ebay_api_error_message(exc=exc)
            raise EbayResponseException(message) from exc

        offer_record = self._ensure_offer_record()
        if offer_record:
            fields: list[str] = []
            if offer_record.successfully_created:
                offer_record.successfully_created = False
                fields.append("successfully_created")
            if offer_record.listing_id:
                offer_record.listing_id = None
                fields.append("listing_id")
            if offer_record.listing_status:
                offer_record.listing_status = None
                fields.append("listing_status")
            if fields:
                self._update_offer_fields(offer=offer_record, fields=fields)

        return response

    def delete_inventory_group(self) -> Any:
        key = self.get_parent_remote_sku()
        if self.get_value_only:
            return {"inventory_item_group_key": key}

        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        return api.sell_inventory_delete_inventory_item_group(
            inventory_item_group_key=key,
        )

    def delete_offers_for_remote_products(self, *, remote_products: Sequence[Any]) -> List[Any]:
        results: List[Any] = []
        for remote_product in list(remote_products):
            with self._use_remote_product(remote_product):
                results.append(self.delete_offer())
        return results

    def delete_inventory_for_remote_products(self, *, remote_products: Sequence[Any]) -> List[Any]:
        results: List[Any] = []
        for remote_product in list(remote_products):
            with self._use_remote_product(remote_product):
                results.append(self.delete_inventory())
        return results


class EbayProductPropertyValueMixin(EbayInventoryItemPushMixin):
    """Shared helpers for eBay product property factories."""

    remote_model_class = EbayProductProperty

    def _compute_remote_value(self, *, remote_property: EbayProperty | None) -> str:
        return self._prepare_property_remote_value(
            product_property=self.local_instance,
            remote_property=remote_property,
        )
