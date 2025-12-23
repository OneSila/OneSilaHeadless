from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional

from properties.models import ProductPropertiesRuleItem, ProductProperty, Property
from sales_channels.factories.products.products import (
    RemoteProductCreateFactory,
    RemoteProductSyncFactory,
    RemoteProductDeleteFactory,
    RemoteProductUpdateFactory,
)
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.factories.products.assigns import SheinSalesChannelAssignFactoryMixin
from sales_channels.integrations.shein.factories.products.images import SheinMediaProductThroughUpdateFactory
from sales_channels.integrations.shein.factories.prices import SheinPriceUpdateFactory
from sales_channels.integrations.shein.factories.properties import SheinProductPropertyUpdateFactory
from sales_channels.integrations.shein.exceptions import (
    SheinConfiguratorAttributesLimitError,
    SheinPreValidationError,
    SheinResponseException,
)
from sales_channels.exceptions import PreFlightCheckError
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinInternalProperty,
    SheinProduct,
    SheinProductCategory,
    SheinProductType,
    SheinProductTypeItem,
)
from sales_channels.integrations.shein.models.sales_channels import SheinRemoteCurrency
from sales_channels.models.products import RemoteProduct
from sales_channels.models.logs import RemoteLog
from sales_channels.models import SalesChannelViewAssign

from translations.models import TranslationFieldsMixin
from sales_channels.integrations.shein.models import (
    SheinInternalPropertyOption,
    SheinSalesChannelView,
)


class SheinProductBaseFactory(
    SheinSignatureMixin,
    SheinSalesChannelAssignFactoryMixin,
    RemoteProductSyncFactory,
):
    """Assemble Shein product payloads using existing value-only factories."""

    remote_model_class = SheinProduct
    action_log = RemoteLog.ACTION_UPDATE
    publish_permission_path = "/open-api/goods/product/check-publish-permission"
    publish_or_edit_path = "/open-api/goods/product/publishOrEdit"
    default_dimension_value = "10"
    default_weight_value = 10
    supplier_barcode_type = "EAN"
    _EAN_DIGITS_RE = re.compile(r"\D+")

    def __init__(
        self,
        *,
        sales_channel,
        local_instance,
        view=None,
        remote_instance=None,
        parent_local_instance=None,
        remote_parent_product=None,
        api=None,
        is_switched: bool = False,
        get_value_only: bool = False,
        skip_checks: bool = False,
    ) -> None:
        self.view = view
        self.get_value_only = get_value_only
        self.skip_checks = skip_checks
        self.prices_data: dict[str, dict[str, Any]] = {}
        self.price_info_list: list[dict[str, Any]] = []
        self.image_info: dict[str, Any] = {}
        self.sale_attribute: Optional[dict[str, Any]] = None
        self.sale_attribute_list: list[dict[str, Any]] = []
        self.size_attribute_list: list[dict[str, Any]] = []
        self.product_attribute_list: list[dict[str, Any]] = []
        self.multi_language_name_list: list[dict[str, str]] = []
        self.multi_language_desc_list: list[dict[str, str]] = []
        self.skc_list: list[dict[str, Any]] = []
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            remote_instance=remote_instance,
            parent_local_instance=parent_local_instance,
            remote_parent_product=remote_parent_product,
            api=api,
            is_switched=is_switched,
        )

    # ------------------------------------------------------------------
    # Base hooks
    # ------------------------------------------------------------------
    def get_api(self):
        return getattr(self, "api", None)

    def set_api(self):
        if self.get_value_only:
            return
        super().set_api()

    def serialize_response(self, response):  # type: ignore[override]
        if response is None:
            return {}
        if isinstance(response, dict):
            return response
        json_getter = getattr(response, "json", None)
        if callable(json_getter):
            try:
                return json_getter() or {}
            except Exception:
                return {}
        return {}

    def get_saleschannel_remote_object(self, remote_sku):  # type: ignore[override]
        """Shein does not provide a reliable lookup by SKU for this integration."""
        return None

    def process_product_properties(self):  # type: ignore[override]
        """Shein properties are embedded into the publish payload; skip remote mirror processing."""
        return

    def assign_images(self):  # type: ignore[override]
        """Shein images are embedded into the publish payload; skip remote media assignments."""
        return

    def assign_ean_code(self):  # type: ignore[override]
        """Shein barcode is embedded into the SKU payload; skip remote EAN mirror processing."""
        return

    def preflight_check(self):
        if self.skip_checks:
            return True
        try:
            response = self.shein_post(path=self.publish_permission_path)
            data = response.json() if hasattr(response, "json") else {}
            info = data.get("info") if isinstance(data, dict) else {}
            if isinstance(info, dict):
                can_publish = info.get("canPublishProduct", True)
                if not can_publish:
                    reason = info.get("reason", "Publishing not allowed.")
                    remote_product = getattr(self, "remote_instance", None)
                    if remote_product is not None and hasattr(remote_product, "add_user_error"):
                        remote_product.add_user_error(
                            action=self.action_log,
                            response=reason,
                            payload={},
                            error_traceback="",
                            identifier=f"{self.__class__.__name__}:preflight",
                            remote_product=remote_product,
                        )
                    return False
        except Exception:
            # If the check fails, proceed to allow iterative development.
            return True
        return True

    def set_rule(self):
        self.rule = None
        self.selected_category_id = ""
        self.selected_product_type_id = ""
        self.selected_site_remote_id = ""
        self.use_spu_pic = False

        mapping = (
            SheinProductCategory.objects.filter(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                product=self.local_instance,
            )
            .exclude(remote_id__in=(None, ""))
            .only("remote_id", "product_type_remote_id", "site_remote_id")
            .first()
        )

        if mapping is not None:
            self.selected_category_id = str(getattr(mapping, "remote_id", "") or "").strip()
            self.selected_product_type_id = str(getattr(mapping, "product_type_remote_id", "") or "").strip()

            if self.selected_category_id and not self.selected_product_type_id:
                site_remote_id = str(getattr(mapping, "site_remote_id", "") or "").strip()
                category_qs = SheinCategory.objects.filter(remote_id=self.selected_category_id)
                if site_remote_id:
                    category_qs = category_qs.filter(site_remote_id=site_remote_id)
                inferred = (
                    category_qs.exclude(product_type_remote_id__in=(None, ""))
                    .values_list("product_type_remote_id", flat=True)
                    .first()
                )
                if inferred:
                    self.selected_product_type_id = str(inferred).strip()

        if not self.selected_category_id or not self.selected_product_type_id:
            explicit_remote_rule = getattr(self, "remote_rule", None)
            if explicit_remote_rule is not None:
                if not self.selected_category_id:
                    self.selected_category_id = str(getattr(explicit_remote_rule, "category_id", "") or "").strip()
                if not self.selected_product_type_id:
                    self.selected_product_type_id = str(getattr(explicit_remote_rule, "remote_id", "") or "").strip()

        if not self.selected_category_id or not self.selected_product_type_id:
            self.rule = self.local_instance.get_product_rule(sales_channel=self.sales_channel)
            if not self.rule:
                raise ValueError("Product has no ProductPropertiesRule mapped for Shein.")

            fallback = (
                SheinProductType.objects.filter(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=self.rule,
                )
                .exclude(remote_id__in=(None, ""))
                .first()
            )
            if fallback is not None:
                if not self.selected_category_id:
                    self.selected_category_id = str(getattr(fallback, "category_id", "") or "").strip()
                if not self.selected_product_type_id:
                    self.selected_product_type_id = str(getattr(fallback, "remote_id", "") or "").strip()

        if not self.selected_category_id or not self.selected_product_type_id:
            raise ValueError(
                "Shein category/product type is missing. Set it via SheinProductCategory (category + product_type_id) "
                "or ensure the product rule is mapped to a SheinProductType."
            )

        self.selected_site_remote_id = self._resolve_site_remote_id()
        self.use_spu_pic = self._resolve_use_spu_pic()

    def _resolve_site_remote_id(self) -> str:
        value = (
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.local_instance,
            )
            .exclude(sales_channel_view__remote_id__in=(None, ""))
            .values_list("sales_channel_view__remote_id", flat=True)
            .first()
        )
        return str(value).strip() if value else ""

    @staticmethod
    def _is_blank_html(value: str) -> bool:
        trimmed = (value or "").strip()
        if not trimmed:
            return True
        lowered = trimmed.lower()
        return lowered in {"<p><br></p>", "<p><br/></p>", "<br>", "<br/>"}

    def _resolve_use_spu_pic(self) -> bool:
        if not self.selected_category_id:
            return False

        categories = SheinCategory.objects.filter(remote_id=self.selected_category_id)
        if self.selected_site_remote_id:
            categories = categories.filter(site_remote_id=self.selected_site_remote_id)

        category = categories.only("picture_config").first()
        if category is None:
            return False

        picture_config = getattr(category, "picture_config", None) or []
        if not isinstance(picture_config, list):
            return False

        for entry in picture_config:
            if not isinstance(entry, dict):
                continue
            if entry.get("field_key") == "switch_spu_picture":
                return bool(entry.get("is_true"))

        return False

    # ------------------------------------------------------------------
    # Payload builders
    # ------------------------------------------------------------------
    def _get_default_language(self) -> str:
        company = getattr(self.sales_channel, "multi_tenant_company", None)
        return getattr(company, "language", None) or TranslationFieldsMixin.LANGUAGES[0][0]

    def _build_translations(self):
        translations = list(self.local_instance.translations.all())
        if not translations:
            return

        default_language = self._get_default_language()

        name_by_language: dict[str, str] = {}
        desc_by_language: dict[str, str] = {}

        for translation in translations:
            language = translation.language or default_language
            if translation.name and language not in name_by_language:
                name_by_language[language] = translation.name
            description = translation.description or translation.short_description
            if description:
                existing = desc_by_language.get(language)
                if existing is None or (self._is_blank_html(existing) and not self._is_blank_html(description)):
                    desc_by_language[language] = description

        if name_by_language:
            self.multi_language_name_list = [
                {"language": language, "name": value}
                for language, value in name_by_language.items()
            ]
        if desc_by_language:
            self.multi_language_desc_list = [
                {"language": language, "name": value}
                for language, value in desc_by_language.items()
            ]

    def _collect_product_properties(self) -> Iterable[ProductProperty]:
        configurator_items = (
            list(self._get_configurator_rule_items())
            if self.local_instance.is_configurable()
            else []
        )

        configurator_property_ids = {item.property_id for item in configurator_items}
        variation_properties: dict[int, dict[int, ProductProperty]] = {}

        if self.local_instance.is_configurable() and configurator_property_ids:
            variations = list(self.local_instance.get_configurable_variations(active_only=True))
            variation_properties = self._prefetch_variation_properties(
                variations=variations,
                property_ids=configurator_property_ids,
            )
            varying_map = self._collect_configurator_values(
                variation_properties=variation_properties,
                property_ids=configurator_property_ids,
            )
            varying_ids = [pid for pid, values in varying_map.items() if len(values) > 1]
            if len(varying_ids) > 3:
                raise SheinConfiguratorAttributesLimitError(
                    "Shein supports at most three sales attributes in total (one SKC-level, up to two SKU-level)."
                )

        rule_properties_ids = (
            self.local_instance.get_required_and_optional_properties(
                product_rule=self.rule,
                sales_channel=self.sales_channel,
            )
            .exclude(type__in=(ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR, ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR))
            .values_list("property_id", flat=True)
        )

        base_properties: list[ProductProperty] = []
        shared_properties: list[ProductProperty] = []
        if self.local_instance.is_configurable():
            shared_properties = list(
                self.local_instance.get_properties_for_configurable_product(
                    product_rule=self.rule,
                    sales_channel=self.sales_channel,
                )
            )
            base_properties = shared_properties
        else:
            base_properties = list(
                ProductProperty.objects.filter_multi_tenant(
                    self.sales_channel.multi_tenant_company
                ).filter(product=self.local_instance, property_id__in=rule_properties_ids)
            )

        seen_ids: set[int] = set()
        combined: list[ProductProperty] = []
        for prop in base_properties + shared_properties:
            if prop.id in seen_ids:
                continue
            seen_ids.add(prop.id)
            combined.append(prop)

        return combined

    def _get_configurator_rule_items(self) -> Iterable[ProductPropertiesRuleItem]:
        return self.local_instance.get_configurator_properties(
            product_rule=self.rule,
            sales_channel=self.sales_channel,
            public_information_only=False,
        )

    def _prefetch_variation_properties(
        self,
        *,
        variations: list,
        property_ids: set[int],
    ) -> dict[int, dict[int, ProductProperty]]:
        if not variations or not property_ids:
            return {}

        props = (
            ProductProperty.objects.filter_multi_tenant(self.sales_channel.multi_tenant_company)
            .filter(product__in=variations, property_id__in=property_ids)
            .select_related("property", "value_select")
            .prefetch_related("value_multi_select")
        )
        mapped: dict[int, dict[int, ProductProperty]] = {}
        for product_property in props:
            mapped.setdefault(product_property.product_id, {})[product_property.property_id] = product_property
        return mapped

    def _serialize_property_value(self, *, product_property: ProductProperty):
        prop = product_property.property
        if prop.type == Property.TYPES.MULTISELECT:
            ids = tuple(sorted(product_property.value_multi_select.values_list("id", flat=True)))
            return ("multi", ids)
        if prop.type == Property.TYPES.SELECT:
            return ("select", product_property.value_select_id)
        value = product_property.get_value()
        if value in (None, "", []):
            return None
        return ("value", str(value))

    def _collect_configurator_values(
        self,
        *,
        variation_properties: dict[int, dict[int, ProductProperty]],
        property_ids: set[int],
    ) -> dict[int, set]:
        values: dict[int, set] = {pid: set() for pid in property_ids}
        for prop_map in variation_properties.values():
            for property_id, product_property in prop_map.items():
                serialized = self._serialize_property_value(product_property=product_property)
                if serialized is None:
                    continue
                values.setdefault(property_id, set()).add(serialized)
        return values

    def _resolve_type_item_for_property(
        self,
        *,
        product_property: ProductProperty,
    ) -> Optional[SheinProductTypeItem]:
        return (
            SheinProductTypeItem.objects.filter(
                product_type__sales_channel=self.sales_channel,
                product_type__remote_id=self.selected_product_type_id,
                property__local_instance=product_property.property,
            )
            .select_related("property")
            .first()
        )

    def _build_property_payloads(self):
        for product_property in self._collect_product_properties():
            type_item = self._resolve_type_item_for_property(product_property=product_property)
            if not type_item:
                continue

            factory = SheinProductPropertyUpdateFactory(
                sales_channel=self.sales_channel,
                local_instance=product_property,
                remote_product=self.remote_instance,
                product_type_item=type_item,
                get_value_only=True,
                skip_checks=True,
            )
            factory.run()
            if not factory.remote_value:
                continue

            try:
                payload = json.loads(factory.remote_value)
            except (TypeError, ValueError):
                continue

            attribute_type = payload.get("attribute_type")

            if attribute_type == SheinProductTypeItem.AttributeType.SALES:
                cleaned_payload = {k: v for k, v in payload.items() if v not in (None, "", [], {})}
                if not cleaned_payload:
                    continue
                if type_item.is_main_attribute and not self.sale_attribute:
                    self.sale_attribute = cleaned_payload
                else:
                    self.sale_attribute_list.append(cleaned_payload)
            elif attribute_type == SheinProductTypeItem.AttributeType.SIZE:
                for entry in self._expand_attribute_payloads(payload=payload):
                    self.size_attribute_list.append(entry)
            else:
                for entry in self._expand_attribute_payloads(payload=payload):
                    self.product_attribute_list.append(entry)

    def _build_prices(self):
        assigns = list(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.local_instance,
            ).select_related("sales_channel_view")
        )
        price_factory = SheinPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_instance,
            get_value_only=True,
            skip_checks=True,
            assigns=assigns,
        )
        price_factory.run()
        self.prices_data = getattr(price_factory, "price_data", {}) or {}
        self.price_info_list = price_factory.value.get("price_info_list", []) if price_factory.value else []

    def _build_media(self):
        media_factory = SheinMediaProductThroughUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=None,
            remote_product=self.remote_instance,
            get_value_only=True,
            skip_checks=True,
        )
        media_factory.run()
        self.image_info = media_factory.value.get("image_info", {}) if media_factory.value else {}

    def _resolve_default_view_assign(self, *, assigns: Iterable[SalesChannelViewAssign]) -> Optional[SalesChannelViewAssign]:
        default_assign = next(
            (assign for assign in assigns if getattr(assign.sales_channel_view, "is_default", False)),
            None,
        )
        return default_assign or (assigns[0] if assigns else None)

    def _get_starting_stock_quantity(self) -> int:
        starting_stock = getattr(self.sales_channel, "starting_stock", None)
        if starting_stock is None:
            return 0
        if not getattr(self.local_instance, "active", True):
            return 0
        try:
            return max(int(starting_stock), 0)
        except (TypeError, ValueError):
            return 0

    def _resolve_supplier_warehouse_id(self, *, assigns: list[SalesChannelViewAssign]) -> str:
        for assign in assigns:
            view = getattr(assign, "sales_channel_view", None)
            resolved = view.get_real_instance() if hasattr(view, "get_real_instance") else view
            key = getattr(resolved, "merchant_location_key", None) if resolved is not None else None
            if key:
                value = str(key).strip()
                if value:
                    return value
        return ""

    def _build_stock_info_list(self, *, assigns: list[SalesChannelViewAssign]) -> list[dict[str, Any]]:
        entry: dict[str, Any] = {"inventory_num": self._get_starting_stock_quantity()}
        warehouse_id = self._resolve_supplier_warehouse_id(assigns=assigns)
        if warehouse_id:
            entry["supplier_warehouse_id"] = warehouse_id
        return [entry]

    def _get_assign_currency_map(self, *, assigns: list[SalesChannelViewAssign]) -> dict[str, str]:
        """Map sub_site -> currency ISO code (e.g. shein-us -> USD)."""
        view_pairs: list[tuple[str, Any]] = []
        view_ids: list[int] = []

        for assign in assigns:
            sub_site = getattr(assign.sales_channel_view, "remote_id", None)
            if not sub_site:
                continue
            view = getattr(assign, "sales_channel_view", None)
            resolved_view = view.get_real_instance() if hasattr(view, "get_real_instance") else view
            if resolved_view is None:
                continue
            view_pairs.append((str(sub_site).strip(), resolved_view))
            if getattr(resolved_view, "id", None):
                view_ids.append(resolved_view.id)

        global_currency_code: Optional[str] = None
        global_codes = (
            SheinRemoteCurrency.objects.filter(
                sales_channel=self.sales_channel,
                sales_channel_view__isnull=True,
            )
            .exclude(remote_code__in=(None, ""))
            .values_list("remote_code", flat=True)
            .distinct()
        )
        if global_codes.count() == 1:
            global_currency_code = str(global_codes.first()).strip()  # type: ignore[arg-type]

        currency_by_view_id: dict[int, str] = {}
        if view_ids:
            rows = (
                SheinRemoteCurrency.objects.filter(
                    sales_channel=self.sales_channel,
                    sales_channel_view_id__in=view_ids,
                )
                .exclude(remote_code__in=(None, ""))
                .values_list("sales_channel_view_id", "remote_code")
            )
            currency_by_view_id = {view_id: str(code).strip() for view_id, code in rows if view_id and code}

        currency_map: dict[str, str] = {}
        for sub_site, resolved_view in view_pairs:
            code = currency_by_view_id.get(getattr(resolved_view, "id", None))
            if not code:
                raw_data = getattr(resolved_view, "raw_data", {}) or {}
                if isinstance(raw_data, dict):
                    code = raw_data.get("currency")
            if not code and global_currency_code:
                code = global_currency_code
            if code:
                currency_map[sub_site] = str(code).strip()

        return {k: v for k, v in currency_map.items() if k and v}

    def _build_sku_price_info_list(self, *, assigns: list[SalesChannelViewAssign]) -> list[dict[str, Any]]:
        if not self.price_info_list:
            return []

        currency_map = self._get_assign_currency_map(assigns=assigns)
        if assigns and not currency_map:
            raise PreFlightCheckError(
                "Shein currency mapping is missing for assigned sub-sites. Pull Shein site list metadata first."
            )

        price_by_currency = {entry.get("currency"): entry for entry in self.price_info_list if entry.get("currency")}

        entries: list[dict[str, Any]] = []
        missing: list[str] = []
        for assign in assigns:
            sub_site = getattr(assign.sales_channel_view, "remote_id", None)
            if not sub_site:
                continue

            sub_site_code = str(sub_site).strip()
            currency_code = currency_map.get(sub_site_code)
            if not currency_code:
                missing.append(sub_site_code)
                continue

            price = price_by_currency.get(currency_code)
            if not price:
                continue

            entry = {
                "currency": currency_code,
                "base_price": price.get("base_price"),
                "special_price": price.get("special_price"),
                "sub_site": sub_site_code,
            }
            if entry["base_price"] is None:
                continue
            entries.append({k: v for k, v in entry.items() if v not in (None, "", [])})

        if missing:
            raise PreFlightCheckError(
                "Shein currency mapping is missing for sub-sites: " + ", ".join(sorted(set(missing)))
            )

        return entries

    # ------------------------------------------------------------------
    # Internal property lookups
    # ------------------------------------------------------------------
    def _get_internal_property_value(self, *, code: str, default: Any, product=None) -> Any:
        product = product or self.local_instance
        internal_prop = (
            SheinInternalProperty.objects.filter(
                sales_channel=self.sales_channel,
                code=code,
            )
            .select_related("local_instance")
            .first()
        )
        if not internal_prop or not internal_prop.local_instance:
            return default

        product_property = ProductProperty.objects.filter(
            product=product,
            property=internal_prop.local_instance,
        ).first()
        if not product_property:
            return default

        value = product_property.get_value()
        return value if value not in (None, "", []) else default

    def _get_internal_property_option_value(self, *, code: str, product=None) -> str | None:
        product = product or self.local_instance
        internal_prop = (
            SheinInternalProperty.objects.filter(
                sales_channel=self.sales_channel,
                code=code,
            )
            .select_related("local_instance")
            .first()
        )
        if not internal_prop or not internal_prop.local_instance:
            return None

        product_property = (
            ProductProperty.objects.filter(
                product=product,
                property=internal_prop.local_instance,
            )
            .select_related("value_select")
            .first()
        )
        if not product_property or not product_property.value_select_id:
            return None

        option = (
            SheinInternalPropertyOption.objects.filter(
                internal_property=internal_prop,
                local_instance_id=product_property.value_select_id,
            )
            .only("value")
            .first()
        )
        if not option or not option.value:
            return None
        return str(option.value)

    def _build_supplier_barcode(self, *, product=None) -> dict[str, str] | None:
        original_product = self.local_instance
        if product is not None:
            self.local_instance = product
        raw_ean = self.get_ean_code_value()
        self.local_instance = original_product
        if not raw_ean:
            return None

        digits = self._EAN_DIGITS_RE.sub("", str(raw_ean))
        if not digits:
            return None

        return {
            "barcode": digits[:32],
            "barcode_type": self.supplier_barcode_type,
        }

    def _build_fill_configuration_info(self, *, package_type: str | None) -> dict[str, Any] | None:
        if not package_type:
            return None
        return {
            "fill_configuration_tags": ["PACKAGE_TYPE_TO_SKU"],
        }

    def _coerce_dimension_value(self, *, value: Any) -> str:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return str(self.default_dimension_value)
        if numeric <= 0:
            return str(self.default_dimension_value)
        return str(numeric)

    def _coerce_weight_value(self, *, value: Any) -> int:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return int(self.default_weight_value)
        if numeric <= 0:
            return int(self.default_weight_value)
        return int(numeric)

    def _resolve_dimensions(self, *, product=None) -> tuple[str, str, str, int]:
        height = self._get_internal_property_value(code="height", default=self.default_dimension_value, product=product)
        length = self._get_internal_property_value(code="length", default=self.default_dimension_value, product=product)
        width = self._get_internal_property_value(code="width", default=self.default_dimension_value, product=product)
        weight = self._get_internal_property_value(code="weight", default=self.default_weight_value, product=product)

        return (
            self._coerce_dimension_value(value=height),
            self._coerce_dimension_value(value=length),
            self._coerce_dimension_value(value=width),
            self._coerce_weight_value(value=weight),
        )

    def _build_suggested_retail_price(self, *, assigns: list[SalesChannelViewAssign]) -> Optional[dict[str, Any]]:
        if not self.price_info_list:
            return None

        preferred_currency: Optional[str] = None
        default_assign = self._resolve_default_view_assign(assigns=assigns)
        if default_assign is not None:
            currency_map = self._get_assign_currency_map(assigns=[default_assign])
            preferred_currency = next(iter(currency_map.values()), None)

        candidates = self.price_info_list
        if preferred_currency:
            candidates = [entry for entry in candidates if entry.get("currency") == preferred_currency]

        for entry in candidates:
            if entry.get("base_price") is None:
                continue
            return {"currency": entry.get("currency"), "price": entry.get("base_price")}

        return None

    def _clean_sale_attribute_payload(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = {
            "attribute_id",
            "attribute_value_id",
            "attribute_extra_value",
            "custom_attribute_value",
            "language",
        }
        return {k: v for k, v in payload.items() if k in allowed_keys and v not in (None, "", [], {})}

    def _expand_attribute_payloads(self, *, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Split multi-select attribute payloads into multiple entries."""

        def _to_list(value: Any) -> Optional[list[Any]]:
            if isinstance(value, (list, tuple)):
                return list(value)
            return None

        value_ids = _to_list(payload.get("attribute_value_id"))
        extra_values = _to_list(payload.get("attribute_extra_value"))
        custom_values = _to_list(payload.get("custom_attribute_value"))

        if not any((value_ids, extra_values, custom_values)):
            return [{k: v for k, v in payload.items() if v not in (None, "", [], {})}]

        max_len = max(len(lst) for lst in (value_ids or [], extra_values or [], custom_values or []) if lst)  # type: ignore[arg-type]
        expanded: list[dict[str, Any]] = []
        for idx in range(max_len):
            entry = dict(payload)
            if value_ids is not None:
                entry["attribute_value_id"] = value_ids[idx] if idx < len(value_ids) else None
            if extra_values is not None:
                entry["attribute_extra_value"] = extra_values[idx] if idx < len(extra_values) else None
            if custom_values is not None:
                entry["custom_attribute_value"] = custom_values[idx] if idx < len(custom_values) else None
            expanded.append({k: v for k, v in entry.items() if v not in (None, "", [], {})})

        return expanded

    def _build_sale_attribute_payload(self, *, product_property: ProductProperty) -> dict[str, Any]:
        type_item = self._resolve_type_item_for_property(product_property=product_property)
        if not type_item:
            raise PreFlightCheckError("Shein product type item mapping is missing for a configurator property.")

        factory = SheinProductPropertyUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=product_property,
            remote_product=self.remote_instance,
            product_type_item=type_item,
            get_value_only=True,
            skip_checks=True,
        )
        remote_value = factory.get_remote_value()
        if not remote_value:
            raise PreFlightCheckError("Unable to render Shein sale attribute payload for a configurator property.")

        try:
            raw_payload = json.loads(remote_value)
        except (TypeError, ValueError):
            raise PreFlightCheckError("Invalid Shein sale attribute payload for configurator property.")
        return self._clean_sale_attribute_payload(payload=raw_payload)

    def _find_sample_property_for_id(
        self,
        *,
        property_id: int,
        variation_properties: dict[int, dict[int, ProductProperty]],
    ) -> Optional[ProductProperty]:
        for props in variation_properties.values():
            if property_id in props:
                return props[property_id]
        return None

    def _is_main_sales_attribute(
        self,
        *,
        property_id: int,
        variation_properties: dict[int, dict[int, ProductProperty]],
    ) -> bool:
        sample_property = self._find_sample_property_for_id(
            property_id=property_id,
            variation_properties=variation_properties,
        )
        if not sample_property:
            return False
        type_item = self._resolve_type_item_for_property(product_property=sample_property)
        return bool(type_item and getattr(type_item, "is_main_attribute", False))

    def _resolve_primary_secondary_attributes(
        self,
        *,
        configurator_items: list[ProductPropertiesRuleItem],
        variation_properties: dict[int, dict[int, ProductProperty]],
        varying_map: dict[int, set],
    ) -> tuple[Optional[ProductPropertiesRuleItem], Optional[ProductPropertiesRuleItem]]:
        primary, sku_items = self._resolve_primary_and_sku_attributes(
            configurator_items=configurator_items,
            variation_properties=variation_properties,
            varying_map=varying_map,
        )
        return primary, (sku_items[0] if sku_items else None)

    def _resolve_primary_and_sku_attributes(
        self,
        *,
        configurator_items: list[ProductPropertiesRuleItem],
        variation_properties: dict[int, dict[int, ProductProperty]],
        varying_map: dict[int, set],
    ) -> tuple[Optional[ProductPropertiesRuleItem], list[ProductPropertiesRuleItem]]:
        if not configurator_items:
            return None, []

        items = sorted(configurator_items, key=lambda item: getattr(item, "sort_order", 0))

        def is_varying(item: ProductPropertiesRuleItem) -> bool:
            return len(varying_map.get(item.property_id, set())) > 1

        primary = next(
            (
                item
                for item in items
                if self._is_main_sales_attribute(
                    property_id=item.property_id,
                    variation_properties=variation_properties,
                )
                and is_varying(item)
            ),
            None,
        )
        if primary is None:
            primary = next((item for item in items if is_varying(item)), None)
        if primary is None:
            primary = next(
                (
                    item
                    for item in items
                    if self._is_main_sales_attribute(
                        property_id=item.property_id,
                        variation_properties=variation_properties,
                    )
                ),
                None,
            )
        if primary is None:
            primary = items[0]

        sku_level_items = [
            item for item in items if item.property_id != primary.property_id and is_varying(item)
        ]
        if len(sku_level_items) > 2:
            raise SheinConfiguratorAttributesLimitError(
                "Shein supports at most three sales attributes in total (one SKC-level, up to two SKU-level)."
            )
        return primary, sku_level_items

    def _build_sku_list(
        self,
        *,
        assigns: list[SalesChannelViewAssign],
        product=None,
        sale_attributes: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        if sale_attributes and len(sale_attributes) > 2:
            raise SheinConfiguratorAttributesLimitError(
                "Shein supports at most two SKU-level sales attributes per SKU."
            )
        price_info_list = self._build_sku_price_info_list(assigns=assigns) if self.is_create else []
        stock_info_list = self._build_stock_info_list(assigns=assigns) if self.is_create else []
        product = product or self.local_instance
        height, length, width, weight = self._resolve_dimensions(product=product)
        supplier_barcode = self._build_supplier_barcode(product=product)
        package_type = self._get_internal_property_option_value(code="package_type", product=product)

        sku_entry: dict[str, Any] = {
            "mall_state": 1 if product.active else 2,
            "supplier_sku": product.sku,
            "stop_purchase": 1,
            "height": height,
            "length": length,
            "width": width,
            "weight": weight,
            "supplier_barcode": supplier_barcode,
            "package_type": package_type,
            "price_info_list": price_info_list or None,
            "sale_attribute_list": sale_attributes or None,
            "stock_info_list": stock_info_list or None,
        }
        return [{k: v for k, v in sku_entry.items() if v not in (None, "", [], {})}]

    def _build_skc_list(self):
        assigns = list(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.local_instance,
            ).select_related("sales_channel_view")
        )
        if not assigns:
            self.skc_list = []
            return

        include_skc_images = not getattr(self, "use_spu_pic", False)

        if not self.local_instance.is_configurable():
            skc_entry: dict[str, Any] = {
                "shelf_way": "1",
                "image_info": (self.image_info or None) if include_skc_images else None,
                "sale_attribute": self.sale_attribute,
                "supplier_code": self.local_instance.sku,
                "sku_list": self._build_sku_list(assigns=assigns),
            }

            suggested_price = self._build_suggested_retail_price(assigns=assigns)
            if suggested_price:
                skc_entry["suggested_retail_price"] = suggested_price

            self.skc_list = [{k: v for k, v in skc_entry.items() if v not in (None, "", [], {})}]
            return

        configurator_items = list(self._get_configurator_rule_items())
        if not configurator_items:
            self.skc_list = []
            return

        variations = list(self.local_instance.get_configurable_variations(active_only=True))
        if not variations:
            self.skc_list = []
            return

        property_ids = {item.property_id for item in configurator_items}
        variation_properties = self._prefetch_variation_properties(
            variations=variations,
            property_ids=property_ids,
        )
        varying_map = self._collect_configurator_values(
            variation_properties=variation_properties,
            property_ids=property_ids,
        )
        varying_ids = [pid for pid, values in varying_map.items() if len(values) > 1]
        if len(varying_ids) > 3:
            raise SheinConfiguratorAttributesLimitError(
                "Shein supports at most three sales attributes in total (one SKC-level, up to two SKU-level)."
            )
        primary_item, sku_level_items = self._resolve_primary_and_sku_attributes(
            configurator_items=configurator_items,
            variation_properties=variation_properties,
            varying_map=varying_map,
        )

        if primary_item is None:
            self.skc_list = []
            return

        grouped: dict[str, dict[str, Any]] = {}
        for variation in variations:
            primary_prop = variation_properties.get(variation.id, {}).get(primary_item.property_id)
            if primary_prop is None:
                raise PreFlightCheckError(
                    f"Missing primary configurator attribute for variation {variation.sku}."
                )
            sale_attr = self._build_sale_attribute_payload(product_property=primary_prop)
            if not sale_attr:
                raise PreFlightCheckError(f"Unable to build Shein sale attribute for variation {variation.sku}.")
            key = json.dumps(sale_attr, sort_keys=True)
            grouped.setdefault(key, {"sale_attribute": sale_attr, "variations": []})
            grouped[key]["variations"].append(variation)

        skc_entries: list[dict[str, Any]] = []
        for data in grouped.values():
            sale_attribute = data["sale_attribute"]
            skc_variations: list = data["variations"]

            sku_entries: list[dict[str, Any]] = []
            for variation in skc_variations:
                sku_sale_attributes: list[dict[str, Any]] = []
                for sku_item in sku_level_items:
                    secondary_prop = variation_properties.get(variation.id, {}).get(sku_item.property_id)
                    if secondary_prop is None:
                        raise PreFlightCheckError(
                            f"Missing SKU-level configurator attribute for variation {variation.sku}."
                        )
                    secondary_attr = self._build_sale_attribute_payload(product_property=secondary_prop)
                    if secondary_attr:
                        sku_sale_attributes.append(secondary_attr)

                sku_entries.extend(
                    self._build_sku_list(
                        assigns=assigns,
                        product=variation,
                        sale_attributes=sku_sale_attributes or None,
                    )
                )

            skc_entry: dict[str, Any] = {
                "shelf_way": "1",
                "image_info": (self.image_info or None) if include_skc_images else None,
                "sale_attribute": sale_attribute,
                "supplier_code": skc_variations[0].sku if skc_variations else self.local_instance.sku,
                "sku_list": sku_entries,
            }

            suggested_price = self._build_suggested_retail_price(assigns=assigns)
            if suggested_price:
                skc_entry["suggested_retail_price"] = suggested_price

            skc_entries.append({k: v for k, v in skc_entry.items() if v not in (None, "", [], {})})

        self.skc_list = skc_entries

    def _attach_size_attribute_relations(self):
        """Attach SKU-level sale attribute references to size attributes when needed."""
        if not self.size_attribute_list or not self.local_instance.is_configurable():
            return

        sku_sale_pairs: set[tuple[Any, Any]] = set()
        for skc in self.skc_list or []:
            for sku in skc.get("sku_list") or []:
                for sale_attr in sku.get("sale_attribute_list") or []:
                    attribute_id = sale_attr.get("attribute_id")
                    value_id = sale_attr.get("attribute_value_id")
                    if attribute_id in (None, "") or value_id in (None, ""):
                        continue
                    sku_sale_pairs.add((attribute_id, value_id))

        if not sku_sale_pairs:
            return

        expanded: list[dict[str, Any]] = []
        for entry in self.size_attribute_list:
            for attribute_id, value_id in sku_sale_pairs:
                payload = dict(entry)
                payload["relate_sale_attribute_id"] = attribute_id
                payload["relate_sale_attribute_value_id"] = value_id
                expanded.append({k: v for k, v in payload.items() if v not in (None, "", [], {})})

        self.size_attribute_list = expanded

    def build_payload(self):
        if not getattr(self, "selected_category_id", None):
            self.set_rule()
        self._build_property_payloads()
        self._build_prices()
        self._build_media()
        self._build_translations()
        self._build_skc_list()
        self._attach_size_attribute_relations()

        self.site_list = self.build_site_list(product=self.local_instance) if self.is_create else []
        package_type = self._get_internal_property_option_value(code="package_type")
        fill_configuration_info = self._build_fill_configuration_info(package_type=package_type)

        self.payload: dict[str, Any] = {
            "category_id": self.selected_category_id,
            "product_type_id": self.selected_product_type_id,
            "supplier_code": self.local_instance.sku,
            "source_system": "openapi",
            "site_list": self.site_list or None,
            "multi_language_name_list": self.multi_language_name_list or None,
            "multi_language_desc_list": self.multi_language_desc_list or None,
            "is_spu_pic": True if getattr(self, "use_spu_pic", False) else None,
            "image_info": (self.image_info or None) if getattr(self, "use_spu_pic", False) else None,
            "sale_attribute": self.sale_attribute,
            "sale_attribute_list": self.sale_attribute_list or None,
            "size_attribute_list": self.size_attribute_list or None,
            "product_attribute_list": self.product_attribute_list or None,
            "skc_list": self.skc_list or None,
            "fill_configuration_info": fill_configuration_info,
        }
        if not self.is_create:
            self.payload["spu_name"] = getattr(self.remote_instance, "remote_id", "") or ""

        # Clean None entries
        self.payload = {k: v for k, v in self.payload.items() if v not in (None, [], {})}
        return self.payload

    # ------------------------------------------------------------------
    # Remote actions
    # ------------------------------------------------------------------
    def perform_remote_action(self):
        self.value = getattr(self, "payload", {})
        if self.get_value_only:
            return self.value

        if getattr(self, "is_create", False):
            try:
                print("[Shein] publishOrEdit payload:", json.dumps(self.value, ensure_ascii=False, sort_keys=True))
            except Exception:
                print("[Shein] publishOrEdit payload:", self.value)

        response = self.shein_post(
            path=self.publish_or_edit_path,
            payload=self.value,
        )
        response_data = response.json() if hasattr(response, "json") else {}
        if getattr(self, "is_create", False):
            try:
                print("[Shein] publishOrEdit response:", json.dumps(response_data, ensure_ascii=False, sort_keys=True))
            except Exception:
                print("[Shein] publishOrEdit response:", response_data)

        if isinstance(response_data, dict):
            code = response_data.get("code")
            msg = (response_data.get("msg") or "").strip()
            info = response_data.get("info")

            is_ok_code = code in ("0", 0)
            is_ok_msg = msg == "OK"

            if isinstance(info, dict) and info.get("success") is False:
                lines: list[str] = []
                for record in info.get("pre_valid_result") or []:
                    if not isinstance(record, dict):
                        continue
                    form_name = str(record.get("form_name") or record.get("form") or "").strip()
                    messages = record.get("messages") or []
                    if not isinstance(messages, list):
                        messages = [messages]
                    for message in messages:
                        text = str(message or "").strip()
                        if not text:
                            continue
                        if form_name:
                            lines.append(f"{form_name}: {text}")
                        else:
                            lines.append(text)

                combined = "\n".join(dict.fromkeys(lines)) if lines else "Shein pre-validation failed."
                raise SheinPreValidationError(combined)

            if info is None and not is_ok_msg:
                raise SheinResponseException(msg or "Shein API returned an error response.")

            if not is_ok_code and not is_ok_msg:
                raise SheinResponseException(msg or f"Shein API returned error code {code}.")


        self.set_remote_id(response_data)
        self._log_submission_tracking(response_data=response_data)
        self._update_or_create_remote_variations(response_data=response_data)
        return response_data

    def _log_submission_tracking(self, *, response_data: Any) -> None:
        if not self.remote_instance or not isinstance(response_data, dict):
            return

        info = response_data.get("info")
        if not isinstance(info, dict):
            info = response_data

        version = info.get("version")
        document_sn = info.get("document_sn") or info.get("documentSn")

        if not version and not document_sn:
            return

        self.remote_instance.add_log(
            action=self.action_log,
            response={"version": version, "document_sn": document_sn},
            payload={"version": version, "document_sn": document_sn},
            identifier="SheinProductSubmission",
            remote_product=self.remote_instance,
        )

    def _update_or_create_remote_variations(self, *, response_data: Any) -> None:
        if not self.local_instance.is_configurable():
            return
        if not isinstance(response_data, dict) or not self.remote_instance:
            return

        info = response_data.get("info") if isinstance(response_data.get("info"), dict) else response_data
        if not isinstance(info, dict):
            return

        spu_name = str(info.get("spu_name") or getattr(self.remote_instance, "spu_name", "") or "").strip()
        skc_list = info.get("skc_list") or []
        if not skc_list:
            return

        variations = {variation.sku: variation for variation in self.local_instance.get_configurable_variations(active_only=True)}

        for skc in skc_list:
            if not isinstance(skc, dict):
                continue
            skc_name = str(skc.get("skc_name") or "").strip()
            for sku_entry in skc.get("sku_list") or []:
                if not isinstance(sku_entry, dict):
                    continue

                supplier_sku = str(
                    sku_entry.get("supplier_sku")
                    or sku_entry.get("supplierSku")
                    or sku_entry.get("supplierSkuCode")
                    or ""
                ).strip()
                if not supplier_sku:
                    continue

                variation = variations.get(supplier_sku)
                if variation is None:
                    continue

                sku_code = str(sku_entry.get("sku_code") or sku_entry.get("skuCode") or "").strip()

                remote_variation, _ = self.remote_model_class.objects.get_or_create(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                    sales_channel=self.sales_channel,
                    local_instance=variation,
                    remote_parent_product=self.remote_instance,
                    is_variation=True,
                    defaults={"remote_sku": supplier_sku},
                )

                update_fields: set[str] = set()
                if not getattr(remote_variation, "remote_sku", None):
                    remote_variation.remote_sku = supplier_sku
                    update_fields.add("remote_sku")

                if sku_code:
                    remote_variation.remote_id = sku_code
                    setattr(remote_variation, "sku_code", sku_code)
                    update_fields.update({"remote_id", "sku_code"})

                if skc_name:
                    setattr(remote_variation, "skc_name", skc_name)
                    update_fields.add("skc_name")

                if spu_name:
                    setattr(remote_variation, "spu_name", spu_name)
                    update_fields.add("spu_name")

                if update_fields:
                    remote_variation.save(update_fields=list(update_fields))

                remote_variation.status = remote_variation.STATUS_PENDING_APPROVAL
                remote_variation.save(update_fields=["status"], skip_status_check=False)

    def set_discount(self):
        """Shein payload includes special_price directly; nothing extra."""
        return

    def update_multi_currency_prices(self):  # type: ignore[override]
        """Update additional storefront currencies via the dedicated price API.

        Shein publish payload already includes prices, but the base product factory expects a hook
        to push additional currencies when multiple currencies are present.
        """

        assigns = list(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.local_instance,
            ).select_related("sales_channel_view")
        )
        currency_map = self._get_assign_currency_map(assigns=assigns)
        used_currency_codes = {code for code in currency_map.values() if code}
        if len(used_currency_codes) <= 1:
            return

        price_factory = SheinPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_instance,
            get_value_only=False,
            skip_checks=True,
            assigns=assigns,
        )
        price_factory.run()


class SheinProductUpdateFactory(SheinProductBaseFactory, RemoteProductUpdateFactory):
    """Resync an existing Shein product."""

    action_log = RemoteLog.ACTION_UPDATE

    def update_remote(self):
        return self.perform_remote_action()


class SheinProductCreateFactory(SheinProductBaseFactory, RemoteProductCreateFactory):
    """Create a Shein product or fall back to sync."""

    action_log = RemoteLog.ACTION_CREATE
    sync_product_factory = SheinProductUpdateFactory

    def create_remote(self):
        return self.perform_remote_action()

    def set_remote_id(self, response_data):
        if not self.remote_instance or not isinstance(response_data, dict):
            return

        info = response_data.get("info")
        if not isinstance(info, dict):
            return

        spu_name = (info.get("spu_name") or "").strip()
        skc_list = info.get("skc_list") or []

        skc_name: str = ""
        sku_code: str = ""
        if isinstance(skc_list, list) and skc_list:
            first_skc = skc_list[0] if isinstance(skc_list[0], dict) else {}
            skc_name = str(first_skc.get("skc_name") or "").strip()
            sku_list = first_skc.get("sku_list") or []
            if isinstance(sku_list, list) and sku_list:
                first_sku = sku_list[0] if isinstance(sku_list[0], dict) else {}
                sku_code = str(first_sku.get("sku_code") or "").strip()

        update_fields: set[str] = set()
        if spu_name:
            self.remote_instance.remote_id = spu_name
            setattr(self.remote_instance, "spu_name", spu_name)
            update_fields.update({"remote_id", "spu_name"})
        if skc_name:
            setattr(self.remote_instance, "skc_name", skc_name)
            update_fields.add("skc_name")
        if sku_code:
            setattr(self.remote_instance, "sku_code", sku_code)
            update_fields.add("sku_code")

        print('------------------------------------------ REMOTE ID SETTED')
        print(spu_name)

        if update_fields:
            self.remote_instance.save(update_fields=list(update_fields))

        # Default newly-published products to pending approval until document-state fetch/webhook updates it.
        self.remote_instance.status = self.remote_instance.STATUS_PENDING_APPROVAL
        self.remote_instance.save(update_fields=["status"], skip_status_check=False)
        return


class SheinProductDeleteFactory(SheinSignatureMixin, RemoteProductDeleteFactory):
    """Withdraw Shein products under review."""

    remote_model_class = SheinProduct
    delete_remote_instance = True
    action_log = RemoteLog.ACTION_DELETE
    revoke_path = "/open-api/goods/revoke-product"

    def delete_remote(self):
        spu_name = getattr(self.remote_instance, "remote_id", None)
        if not spu_name:
            return {}

        try:
            response = self.shein_post(
                path=self.revoke_path,
                payload={"spuName": spu_name},
            )
            return response.json() if hasattr(response, "json") else {}
        except Exception as exc:
            # Log as admin error but don't raise to allow local cleanup
            self.remote_instance.add_admin_error(
                action=self.action_log,
                response=str(exc),
                payload={"spuName": spu_name},
                error_traceback="",
                identifier=f"{self.__class__.__name__}:delete_remote",
                remote_product=self.remote_instance,
            )
            return {}
