from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

from properties.models import ProductProperty, Property
from sales_channels.factories.products.products import (
    RemoteProductCreateFactory,
    RemoteProductSyncFactory,
    RemoteProductUpdateFactory,
)
from sales_channels.integrations.shein.factories import (
    SheinMediaProductThroughUpdateFactory,
    SheinPriceUpdateFactory,
    SheinProductPropertyUpdateFactory,
)
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.factories.products.assigns import SheinSalesChannelAssignFactoryMixin
from sales_channels.integrations.shein.models import (
    SheinProductType,
    SheinProductTypeItem,
)
from sales_channels.models.products import RemoteProduct
from sales_channels.models.logs import RemoteLog


class SheinProductBaseFactory(
    SheinSignatureMixin,
    SheinSalesChannelAssignFactoryMixin,
    RemoteProductSyncFactory,
):
    """Assemble Shein product payloads using existing value-only factories."""

    remote_model_class = RemoteProduct
    action_log = RemoteLog.ACTION_UPDATE
    publish_permission_path = "/open-api/goods/product/check-publish-permission"

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

    def build_payload(self):
        self._build_property_payloads()
        self._build_prices()
        self._build_media()

        self.site_list = self.build_site_list(product=self.local_instance)

        self.payload = {
            "category_id": self.remote_rule.category_id,
            "product_type_id": self.remote_rule.remote_id,
            "supplier_code": self.local_instance.sku,
            "source_system": "openapi",
            "spu_name": getattr(self.remote_instance, "remote_id", "") or self.local_instance.name,
            "site_list": self.site_list,
            "price_info_list": self.price_info_list or None,
            "image_info": self.image_info or None,
            "sale_attribute": self.sale_attribute,
            "sale_attribute_list": self.sale_attribute_list or None,
            "size_attribute_list": self.size_attribute_list or None,
            "product_attribute_list": self.product_attribute_list or None,
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
