"""Mirror helpers for Shein product imports."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django.core.exceptions import ValidationError

from imports_exports.factories.products import ImportProductInstance
from products.product_types import CONFIGURABLE
from sales_channels.integrations.shein.models import (
    SheinProduct,
    SheinProductCategory,
    SheinProductProperty,
    SheinSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign
from sales_channels.models.products import RemoteProductConfigurator


class SheinProductImportMirrorMixin:
    def update_remote_product(
        self,
        *,
        import_instance: ImportProductInstance,
        spu_payload: Mapping[str, Any],
        skc_payload: Mapping[str, Any] | None,
        sku_payload: Mapping[str, Any] | None,
        is_variation: bool,
    ) -> None:
        remote_product = getattr(import_instance, "remote_instance", None)
        if remote_product is None:
            return

        updates: list[str] = []

        local_sku = import_instance.data.get("sku")
        if not local_sku:
            local_instance = getattr(import_instance, "instance", None)
            if local_instance is None:
                local_instance = getattr(remote_product, "local_instance", None)
            if local_instance is not None and getattr(local_instance, "type", None) == CONFIGURABLE:
                local_sku = getattr(local_instance, "sku", None)
        if local_sku and remote_product.remote_sku != local_sku:
            remote_product.remote_sku = local_sku
            updates.append("remote_sku")

        spu_name = self._extract_spu_name(payload=spu_payload)
        skc_name = self._extract_skc_name(payload=skc_payload)
        sku_code = self._extract_sku_code(payload=sku_payload)

        if spu_name and getattr(remote_product, "spu_name", None) != spu_name:
            setattr(remote_product, "spu_name", spu_name)
            updates.append("spu_name")

        if skc_name and getattr(remote_product, "skc_name", None) != skc_name:
            setattr(remote_product, "skc_name", skc_name)
            updates.append("skc_name")

        if sku_code and getattr(remote_product, "sku_code", None) != sku_code:
            setattr(remote_product, "sku_code", sku_code)
            updates.append("sku_code")

        desired_remote_id = sku_code if is_variation else spu_name
        if desired_remote_id and remote_product.remote_id != desired_remote_id:
            remote_product.remote_id = desired_remote_id
            updates.append("remote_id")

        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation
            updates.append("is_variation")

        if not is_variation and remote_product.remote_parent_product_id is not None:
            remote_product.remote_parent_product = None
            updates.append("remote_parent_product")

        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100
            updates.append("syncing_current_percentage")

        if remote_product.status != remote_product.STATUS_COMPLETED:
            remote_product.status = remote_product.STATUS_COMPLETED
            updates.append("status")

        if updates:
            save_kwargs: dict[str, Any] = {"update_fields": updates}
            if "status" in updates:
                save_kwargs["skip_status_check"] = False
            remote_product.save(**save_kwargs)

    def handle_attributes(self, *, import_instance: ImportProductInstance) -> None:
        if not hasattr(import_instance, "properties"):
            return

        remote_product = getattr(import_instance, "remote_instance", None)
        if remote_product is None:
            return

        mirror_map = import_instance.data.get("__mirror_product_properties_map", {})
        if not isinstance(mirror_map, Mapping):
            mirror_map = {}

        for product_property in getattr(import_instance, "product_property_instances", []):
            local_property = getattr(product_property, "property", None)
            if local_property is None:
                continue

            mirror_data = mirror_map.get(local_property.id)
            if not mirror_data:
                continue

            remote_property = mirror_data.get("remote_property")
            remote_value = mirror_data.get("remote_value")
            if remote_property is None:
                continue

            remote_entry, _ = SheinProductProperty.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=remote_product,
                local_instance=product_property,
                defaults={"remote_property": remote_property},
            )

            updated = False
            if remote_entry.remote_property_id != remote_property.id:
                remote_entry.remote_property = remote_property
                updated = True

            if remote_value is not None and remote_entry.remote_value != remote_value:
                remote_entry.remote_value = remote_value
                updated = True

            if updated:
                remote_entry.save()

    def handle_variations(
        self,
        *,
        import_instance: ImportProductInstance,
        parent_sku: str,
        parent_remote: SheinProduct | None = None,
    ) -> None:
        remote_variation = getattr(import_instance, "remote_instance", None)
        if remote_variation is None or not parent_sku:
            return

        remote_parent = parent_remote
        if remote_parent is None:
            remote_parent = (
                SheinProduct.objects.filter(
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.multi_tenant_company,
                    remote_sku=parent_sku,
                )
                .select_related("local_instance")
                .first()
            )
        if remote_parent is None:
            return

        updated = False
        if not remote_variation.is_variation:
            remote_variation.is_variation = True
            updated = True

        if remote_variation.remote_parent_product_id != remote_parent.id:
            remote_variation.remote_parent_product = remote_parent
            updated = True

        if updated:
            remote_variation.save()

        local_parent = remote_parent.local_instance
        local_variation = remote_variation.local_instance
        if local_parent is not None and local_variation is not None:
            parent_categories = SheinProductCategory.objects.filter(
                product=local_parent,
                sales_channel=self.sales_channel,
            )
            for category in parent_categories:
                try:
                    SheinProductCategory.objects.get_or_create(
                        product=local_variation,
                        multi_tenant_company=self.multi_tenant_company,
                        sales_channel=self.sales_channel,
                        defaults={
                            "remote_id": category.remote_id,
                            "product_type_remote_id": category.product_type_remote_id,
                        },
                    )
                except ValidationError as exc:
                    existing = SheinProductCategory.objects.filter(
                        product=local_variation,
                        sales_channel=self.sales_channel,
                    ).first()
                    if existing is not None:
                        continue
                    self._add_broken_record(
                        code=self.ERROR_INVALID_CATEGORY_ASSIGNMENT,
                        message="Invalid Shein category returned by payload",
                        data={
                            "category_id": category.remote_id,
                            "sku": getattr(local_variation, "sku", None),
                        },
                        context={"product_id": getattr(local_variation, "id", None)},
                        exc=exc,
                    )

        parent_rule = None
        if remote_parent.local_instance is not None:
            parent_rule = remote_parent.local_instance.get_product_rule(
                sales_channel=self.sales_channel,
            )
        if parent_rule is None or remote_parent.local_instance is None:
            return

        variations_queryset = remote_parent.local_instance.get_configurable_variations(active_only=False)

        if hasattr(remote_parent, "configurator"):
            remote_parent.configurator.update_if_needed(
                rule=parent_rule,
                variations=variations_queryset,
                send_sync_signal=False,
            )
        else:
            RemoteProductConfigurator.objects.create_from_remote_product(
                remote_product=remote_parent,
                rule=parent_rule,
                variations=variations_queryset,
            )

    def handle_sales_channels_views(
        self,
        *,
        import_instance: ImportProductInstance,
        structured_data: dict[str, Any],
        spu_payload: Mapping[str, Any],
    ) -> None:
        remote_product = getattr(import_instance, "remote_instance", None)
        local_product = getattr(import_instance, "instance", None)
        if remote_product is None or local_product is None:
            return

        view_payloads = self._collect_view_payloads(spu_payload=spu_payload)
        if not view_payloads:
            return

        for site_code in view_payloads:
            payload = view_payloads.get(site_code) or {}
            link = payload.get("link") if isinstance(payload, Mapping) else None
            view = (
                SheinSalesChannelView.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_id=site_code,
                )
                .select_related()
                .first()
            )
            if view is None:
                continue

            assign, _ = SalesChannelViewAssign.objects.get_or_create(
                product=local_product,
                sales_channel_view=view,
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                defaults={
                    "remote_product": remote_product,
                    "link": link,
                },
            )

            update_fields: list[str] = []
            if assign.remote_product_id != remote_product.id:
                assign.remote_product = remote_product
                update_fields.append("remote_product")
            if link and assign.link != link:
                assign.link = link
                update_fields.append("link")
            if update_fields:
                assign.save(update_fields=update_fields)

        self._sync_product_category(
            product=local_product,
            spu_payload=spu_payload,
        )

    def _sync_product_category(
        self,
        *,
        product: Any | None,
        spu_payload: Mapping[str, Any],
    ) -> None:
        if product is None:
            return

        category_id = self._extract_category_id(payload=spu_payload)
        if not category_id:
            return

        product_type_id = self._extract_product_type_id(payload=spu_payload) or ""

        try:
            mapping, created = SheinProductCategory.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                sales_channel=self.sales_channel,
                defaults={
                    "remote_id": category_id,
                    "product_type_remote_id": product_type_id,
                },
            )
        except ValidationError as exc:
            self._add_broken_record(
                code=self.ERROR_INVALID_CATEGORY_ASSIGNMENT,
                message="Invalid Shein category returned by payload",
                data={
                    "category_id": category_id,
                    "sku": getattr(product, "sku", None),
                },
                context={"product_id": getattr(product, "id", None)},
                exc=exc,
            )
            return

        if created:
            return

        update_fields: list[str] = []
        if mapping.remote_id != category_id:
            mapping.remote_id = category_id
            update_fields.append("remote_id")
        if mapping.product_type_remote_id != product_type_id:
            mapping.product_type_remote_id = product_type_id
            update_fields.append("product_type_remote_id")

        if update_fields:
            try:
                mapping.save(update_fields=update_fields)
            except ValidationError as exc:
                self._add_broken_record(
                    code=self.ERROR_INVALID_CATEGORY_ASSIGNMENT,
                    message="Invalid Shein category returned by payload",
                    data={
                        "category_id": category_id,
                        "sku": getattr(product, "sku", None),
                    },
                    context={"product_id": getattr(product, "id", None)},
                    exc=exc,
                )
