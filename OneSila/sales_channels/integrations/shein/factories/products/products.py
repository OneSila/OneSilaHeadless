from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

from django.db.models import Sum

from properties.models import ProductProperty, Property
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
from sales_channels.integrations.shein.models import (
    SheinInternalProperty,
    SheinProductType,
    SheinProductTypeItem,
)
from sales_channels.models.products import RemoteProduct
from sales_channels.models.logs import RemoteLog
from sales_channels.models import SalesChannelViewAssign

from inventory.models import Inventory
from translations.models import TranslationFieldsMixin
from sales_channels.integrations.shein.models import SheinSalesChannelView


class SheinProductBaseFactory(
    SheinSignatureMixin,
    SheinSalesChannelAssignFactoryMixin,
    RemoteProductSyncFactory,
):
    """Assemble Shein product payloads using existing value-only factories."""

    remote_model_class = RemoteProduct
    action_log = RemoteLog.ACTION_UPDATE
    publish_permission_path = "/open-api/goods/product/check-publish-permission"
    default_dimension_value = "10"
    default_weight_value = 10

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
                    self.sales_channel.add_user_error(
                        action=self.action_log,
                        response=reason,
                        payload={},
                        error_traceback="",
                        identifier=f"{self.__class__.__name__}:preflight",
                        remote_product=getattr(self, "remote_instance", None),
                    )
                    return False
        except Exception:
            # If the check fails, proceed to allow iterative development.
            return True
        return True

    def set_rule(self):
        self.rule = self.local_instance.get_product_rule(sales_channel=self.sales_channel)
        if not self.rule:
            raise ValueError("Product has no ProductPropertiesRule mapped for Shein.")

        product_type = (
            SheinProductType.objects.filter(
                sales_channel=self.sales_channel,
                local_instance=self.rule,
            )
            .exclude(remote_id__isnull=True)
            .first()
        )
        if not product_type:
            raise ValueError("Shein product type mapping is missing for the product rule.")
        self.remote_rule = product_type

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

        name_entries: list[dict[str, str]] = []
        desc_entries: list[dict[str, str]] = []

        for translation in translations:
            language = translation.language or default_language
            if translation.name:
                name_entries.append({"language": language, "name": translation.name})
            description = translation.description or translation.short_description
            if description:
                desc_entries.append({"language": language, "name": description})

        if name_entries:
            self.multi_language_name_list = name_entries
        if desc_entries:
            self.multi_language_desc_list = desc_entries

    def _collect_product_properties(self) -> Iterable[ProductProperty]:
        if self.local_instance.is_configurable():
            return self.local_instance.get_properties_for_configurable_product(
                product_rule=self.rule,
                sales_channel=self.sales_channel,
            )

        rule_properties_ids = self.local_instance.get_required_and_optional_properties(
            product_rule=self.rule,
            sales_channel=self.sales_channel,
        ).values_list("property_id", flat=True)

        return ProductProperty.objects.filter_multi_tenant(
            self.sales_channel.multi_tenant_company
        ).filter(product=self.local_instance, property_id__in=rule_properties_ids)

    def _resolve_type_item_for_property(
        self,
        *,
        product_property: ProductProperty,
    ) -> Optional[SheinProductTypeItem]:
        return (
            SheinProductTypeItem.objects.filter(
                product_type=self.remote_rule,
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
                if type_item.is_main_attribute and not self.sale_attribute:
                    self.sale_attribute = payload
                else:
                    self.sale_attribute_list.append(payload)
            elif attribute_type == SheinProductTypeItem.AttributeType.SIZE:
                self.size_attribute_list.append(payload)
            else:
                self.product_attribute_list.append(payload)

    def _build_prices(self):
        price_factory = SheinPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_instance,
            get_value_only=True,
            skip_checks=True,
        )
        price_factory.run()
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

    def _build_stock_info_list(self, *, assigns: list[SalesChannelViewAssign]) -> list[dict[str, Any]]:
        quantity = (
            Inventory.objects.filter(product=self.local_instance).aggregate(total=Sum("quantity")).get("total") or 0
        )

        default_assign = self._resolve_default_view_assign(assigns=assigns)
        supplier_warehouse_id: Optional[str] = None
        supplier_warehouse_name: Optional[str] = None

        if default_assign and isinstance(default_assign.sales_channel_view, SheinSalesChannelView):
            supplier_warehouse_id = default_assign.sales_channel_view.merchant_location_key
            choices = default_assign.sales_channel_view.merchant_location_choices or []
            for choice in choices:
                if choice.get("warehouseCode") == supplier_warehouse_id:
                    supplier_warehouse_name = choice.get("warehouseName")
                    break

        stock_entry = {
            "inventory_num": int(quantity),
            "supplier_warehouse_id": supplier_warehouse_id,
            "supplier_warehouse_name": supplier_warehouse_name,
        }

        return [{k: v for k, v in stock_entry.items() if v not in (None, "", [])}]

    def _build_sku_price_info_list(self, *, assigns: list[SalesChannelViewAssign]) -> list[dict[str, Any]]:
        if not self.price_info_list:
            return []

        entries: list[dict[str, Any]] = []
        for assign in assigns:
            sub_site = getattr(assign.sales_channel_view, "remote_id", None)
            if not sub_site:
                continue

            # Try to map currency per site; fall back to all price entries.
            view_currency_code: Optional[str] = None
            if isinstance(assign.sales_channel_view, SheinSalesChannelView):
                raw_data = getattr(assign.sales_channel_view, "raw_data", {}) or {}
                view_currency_code = raw_data.get("currency")

            for price in self.price_info_list:
                currency = price.get("currency")
                if view_currency_code and currency and currency != view_currency_code:
                    continue

                entry = {
                    "currency": currency,
                    "base_price": price.get("base_price"),
                    "special_price": price.get("special_price"),
                    "sub_site": sub_site,
                }
                if entry["base_price"] is None:
                    continue
                entries.append({k: v for k, v in entry.items() if v not in (None, "", [])})

        return entries

    # ------------------------------------------------------------------
    # Internal property lookups
    # ------------------------------------------------------------------
    def _get_internal_property_value(self, *, code: str, default: Any) -> Any:
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
            product=self.local_instance,
            property=internal_prop.local_instance,
        ).first()
        if not product_property:
            return default

        value = product_property.get_value()
        return value if value not in (None, "", []) else default

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

    def _resolve_dimensions(self) -> tuple[str, str, str, int]:
        height = self._get_internal_property_value(code="height", default=self.default_dimension_value)
        length = self._get_internal_property_value(code="length", default=self.default_dimension_value)
        width = self._get_internal_property_value(code="width", default=self.default_dimension_value)
        weight = self._get_internal_property_value(code="weight", default=self.default_weight_value)

        return (
            self._coerce_dimension_value(value=height),
            self._coerce_dimension_value(value=length),
            self._coerce_dimension_value(value=width),
            self._coerce_weight_value(value=weight),
        )

    def _build_suggested_retail_price(self) -> Optional[dict[str, Any]]:
        if not self.price_info_list:
            return None
        first = self.price_info_list[0]
        if not first.get("base_price"):
            return None
        return {
            "currency": first.get("currency"),
            "price": first.get("base_price"),
        }

    def _build_sku_list(self, *, assigns: list[SalesChannelViewAssign]) -> list[dict[str, Any]]:
        price_info_list = self._build_sku_price_info_list(assigns=assigns)
        stock_info_list = self._build_stock_info_list(assigns=assigns)
        height, length, width, weight = self._resolve_dimensions()

        sku_entry: dict[str, Any] = {
            "mall_state": 1 if self.local_instance.active else 2,
            "sku_code": getattr(self.remote_instance, "remote_id", None) or getattr(self.remote_instance, "remote_sku", None),
            "supplier_sku": self.local_instance.sku,
            "stop_purchase": 1,
            "height": height,
            "length": length,
            "width": width,
            "weight": weight,
            "price_info_list": price_info_list or None,
            "sale_attribute_list": self.sale_attribute_list or None,
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

        skc_entry: dict[str, Any] = {
            "shelf_way": "1",
            "image_info": self.image_info or None,
            "sale_attribute": self.sale_attribute,
            "supplier_code": self.local_instance.sku,
            "sku_list": self._build_sku_list(assigns=assigns),
        }

        suggested_price = self._build_suggested_retail_price()
        if suggested_price:
            skc_entry["suggested_retail_price"] = suggested_price

        self.skc_list = [{k: v for k, v in skc_entry.items() if v not in (None, "", [], {})}]

    def build_payload(self):
        self._build_property_payloads()
        self._build_prices()
        self._build_media()
        self._build_translations()
        self._build_skc_list()

        self.site_list = self.build_site_list(product=self.local_instance)

        self.payload = {
            "category_id": self.remote_rule.category_id,
            "product_type_id": self.remote_rule.remote_id,
            "supplier_code": self.local_instance.sku,
            "source_system": "openapi",
            "spu_name": getattr(self.remote_instance, "remote_id", "") or self.local_instance.name,
            "site_list": self.site_list,
            "multi_language_name_list": self.multi_language_name_list or None,
            "multi_language_desc_list": self.multi_language_desc_list or None,
            "price_info_list": self.price_info_list or None,
            "image_info": self.image_info or None,
            "sale_attribute": self.sale_attribute,
            "sale_attribute_list": self.sale_attribute_list or None,
            "size_attribute_list": self.size_attribute_list or None,
            "product_attribute_list": self.product_attribute_list or None,
            "skc_list": self.skc_list or None,
        }

        # Clean None entries
        self.payload = {k: v for k, v in self.payload.items() if v not in (None, [], {})}
        return self.payload

    # ------------------------------------------------------------------
    # Remote actions
    # ------------------------------------------------------------------
    def perform_remote_action(self):
        # No-op stub until API client is wired; store computed payload.
        self.value = getattr(self, "payload", {})
        if self.get_value_only and self.remote_instance:
            self.remote_instance.remote_value = json.dumps(self.value)
            self.remote_instance.save(update_fields=["remote_value"])
        return self.value

    def set_discount(self):
        """Shein payload includes special_price directly; nothing extra."""
        return


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


class SheinProductDeleteFactory(SheinSignatureMixin, RemoteProductDeleteFactory):
    """Withdraw Shein products under review."""

    remote_model_class = RemoteProduct
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
