"""Shein product import processors."""

from __future__ import annotations

import math
from collections.abc import Iterator, Mapping
from typing import Any

from django.db import IntegrityError

from core.mixins import TemporaryDisableInspectorSignalsMixin
from imports_exports.factories.imports import AsyncProductImportMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.helpers import increment_processed_records
from sales_channels.factories.imports import SalesChannelImportMixin
from sales_channels.integrations.amazon.helpers import serialize_listing_item
from sales_channels.integrations.shein.factories.imports.product_parsers import (
    SheinProductImportPayloadParser,
)
from sales_channels.integrations.shein.factories.imports.product_helpers import (
    SheinProductImportHelpers,
)
from sales_channels.integrations.shein.factories.imports.product_mirrors import (
    SheinProductImportMirrorMixin,
)
from sales_channels.integrations.shein.factories.imports.product_payloads import (
    SheinProductImportPayloadMixin,
)
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.models import (
    SheinImageProductAssociation,
    SheinProduct,
    SheinProductType,
)
from sales_channels.models.products import (
    RemoteEanCode,
    RemotePrice,
    RemoteProductContent,
)


class SheinProductsImportProcessor(
    SheinProductImportMirrorMixin,
    SheinProductImportPayloadMixin,
    SheinProductImportHelpers,
    TemporaryDisableInspectorSignalsMixin,
    SalesChannelImportMixin,
    SheinSignatureMixin,
):
    """Base processor that will orchestrate Shein product imports."""

    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    ERROR_BROKEN_IMPORT_PROCESS = "BROKEN_IMPORT_PROCESS"
    ERROR_INVALID_PRODUCT_DATA = "INVALID_PRODUCT_DATA"
    ERROR_INVALID_CATEGORY_ASSIGNMENT = "INVALID_CATEGORY_ASSIGNMENT"

    remote_ean_code_class = RemoteEanCode
    remote_product_content_class = RemoteProductContent
    remote_imageproductassociation_class = SheinImageProductAssociation
    remote_price_class = RemotePrice

    def __init__(
        self,
        *,
        import_process,
        sales_channel,
        language: str | None = None,
    ) -> None:
        super().__init__(
            import_process=import_process,
            sales_channel=sales_channel,
            language=language,
        )
        self.language = language
        self._spu_index: list[str] | None = None
        self._payload_parser = SheinProductImportPayloadParser(sales_channel=sales_channel)

    def get_api(self):
        return self

    def prepare_import_process(self):
        self.sales_channel.active = False
        self.sales_channel.is_importing = True
        self.sales_channel.save()

        self.import_process.skip_broken_records = True
        self.import_process.save()

    def get_total_instances(self) -> int:
        try:
            total = self.get_total_product_count()
        except Exception:
            total = None

        if total is not None and total != 0:
            return total

        return len(self._load_spu_index())

    def get_products_data(self) -> Iterator[dict[str, Any]]:
        for spu_name in self._load_spu_index():
            try:
                payload = self.get_product(spu_name=spu_name)
            except Exception as exc:
                self._add_broken_record(
                    code=self.ERROR_INVALID_PRODUCT_DATA,
                    message="Unable to fetch Shein product payload",
                    data={"spu_name": spu_name},
                    exc=exc,
                )
                continue

            if isinstance(payload, dict):
                yield {"product": payload}

    def get_product_rule(
        self,
        *,
        product_data: dict[str, Any] | None = None,
    ) -> Any | None:
        if not isinstance(product_data, Mapping):
            return None

        product_type_id = self._extract_product_type_id(payload=product_data)
        category_id = self._extract_category_id(payload=product_data)
        queryset = SheinProductType.objects.filter(
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )

        product_type = None
        if product_type_id:
            product_type = queryset.filter(remote_id=product_type_id).select_related("local_instance").first()
        if product_type is None and category_id:
            product_type = queryset.filter(category_id=category_id).select_related("local_instance").first()

        if product_type and product_type.local_instance:
            return product_type.local_instance

        return None

    def import_products_process(self) -> None:
        for product_payload in self.get_products_data():
            if not isinstance(product_payload, dict):
                continue

            product = product_payload.get("product")
            if not isinstance(product, dict):
                continue

            self.process_product_item(product_data=product)
            self.update_percentage()

    def process_product_item(
        self,
        *,
        product_data: dict[str, Any],
    ) -> None:
        if not isinstance(product_data, dict):
            self._add_broken_record(
                code=self.ERROR_INVALID_PRODUCT_DATA,
                message="Invalid product payload received",
                data={"raw": product_data},
            )
            return

        spu_name = self._extract_spu_name(payload=product_data)
        if not spu_name:
            self._add_broken_record(
                code=self.ERROR_INVALID_PRODUCT_DATA,
                message="Missing spuName on Shein payload",
                data=product_data,
            )
            return

        sku_entries = self._collect_sku_entries(payload=product_data)
        if not sku_entries:
            self._add_broken_record(
                code=self.ERROR_INVALID_PRODUCT_DATA,
                message="No SKU entries returned by Shein payload",
                data={"spu_name": spu_name},
            )
            return

        rule = self.get_product_rule(product_data=product_data)
        is_configurable = len(sku_entries) > 1
        primary_entry = sku_entries[0]
        images_skc_payload = None
        if is_configurable and self.sales_channel.sync_contents:
            raw_spu_images = product_data.get("spuImageInfoList") or product_data.get("spu_image_info_list") or []
            has_spu_images = False
            if isinstance(raw_spu_images, list):
                for entry in raw_spu_images:
                    if isinstance(entry, Mapping):
                        has_spu_images = True
                        break
            if not has_spu_images:
                best_skc_payload = None
                best_count = 0
                for entry in sku_entries:
                    skc_payload = entry.get("skc")
                    if not isinstance(skc_payload, Mapping):
                        continue
                    raw_skc_images = skc_payload.get("skcImageInfoList") or skc_payload.get(
                        "skc_image_info_list"
                    ) or []
                    if not isinstance(raw_skc_images, list):
                        continue
                    image_count = sum(1 for img in raw_skc_images if isinstance(img, Mapping))
                    if image_count > best_count:
                        best_count = image_count
                        best_skc_payload = skc_payload
                if best_skc_payload is not None and best_count:
                    images_skc_payload = best_skc_payload

        parent_instance = self._process_single_product_entry(
            spu_payload=product_data,
            skc_payload=primary_entry.get("skc"),
            sku_payload=primary_entry.get("sku"),
            rule=rule,
            is_variation=False,
            is_configurable=is_configurable,
            parent_sku=spu_name,
            images_skc_payload=images_skc_payload,
        )

        if not is_configurable or parent_instance is None:
            return

        parent_sku = spu_name
        if parent_instance.instance is not None and parent_instance.instance.sku:
            parent_sku = parent_instance.instance.sku

        for entry in sku_entries:
            self._process_single_product_entry(
                spu_payload=product_data,
                skc_payload=entry.get("skc"),
                sku_payload=entry.get("sku"),
                rule=rule,
                is_variation=True,
                is_configurable=False,
                parent_sku=parent_sku,
                parent_remote=parent_instance.remote_instance,
            )


    def _process_single_product_entry(
        self,
        *,
        spu_payload: Mapping[str, Any],
        skc_payload: Mapping[str, Any] | None,
        sku_payload: Mapping[str, Any] | None,
        rule: Any | None,
        is_variation: bool,
        is_configurable: bool,
        parent_sku: str | None,
        parent_remote: SheinProduct | None = None,
        images_skc_payload: Mapping[str, Any] | None = None,
    ) -> ImportProductInstance | None:
        local_sku = None
        if not (is_configurable and not is_variation):
            local_sku = self._resolve_local_sku(
                sku_payload=sku_payload,
                fallback_sku=parent_sku,
            )
            if not local_sku:
                self._add_broken_record(
                    code=self.ERROR_INVALID_PRODUCT_DATA,
                    message="Unable to determine SKU for Shein product entry",
                    data={"spu_name": self._extract_spu_name(payload=spu_payload)},
                )
                return None

        remote_product = self._get_remote_product(
            sku=local_sku,
            spu_payload=spu_payload,
            sku_payload=sku_payload,
            is_variation=is_variation,
        )
        product_instance = remote_product.local_instance if remote_product and remote_product.local_instance else None

        try:
            structured, language, view = self.get__product_data(
                spu_payload=spu_payload,
                skc_payload=skc_payload,
                sku_payload=sku_payload,
                local_sku=local_sku,
                is_variation=is_variation,
                is_configurable=is_configurable,
                images_skc_payload=images_skc_payload,
                product_instance=product_instance,
                parent_sku=parent_sku,
            )
        except ValueError as exc:
            self._add_broken_record(
                code=self.ERROR_INVALID_PRODUCT_DATA,
                message=str(exc) or "Invalid product data returned by Shein",
                data={"sku": local_sku},
                context={"is_variation": is_variation},
                exc=exc,
            )
            return None

        if remote_product and remote_product.local_instance and remote_product.local_instance.type:
            structured["type"] = remote_product.local_instance.type

        instance = ImportProductInstance(
            structured,
            import_process=self.import_process,
            rule=rule,
            sales_channel=self.sales_channel,
            instance=product_instance,
            update_current_rule=False,
        )
        instance.prepare_mirror_model_class(
            mirror_model_class=SheinProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={
                "is_variation": is_variation,
            },
        )
        if local_sku:
            instance.mirror_model_defaults["remote_sku"] = local_sku
        instance.language = language

        try:
            instance.process()
        except IntegrityError as exc:
            context = {
                "sku": instance.data.get("sku", local_sku),
                "is_variation": is_variation,
            }
            self._add_broken_record(
                code=self.ERROR_BROKEN_IMPORT_PROCESS,
                message="Broken import process for SKU",
                data=instance.data,
                context=context,
                exc=exc,
            )

            if remote_product:
                instance.remote_instance = remote_product
                if product_instance:
                    instance.instance = product_instance
            else:
                return None

        if instance.remote_instance is None:
            instance.remote_instance = remote_product

        if instance.remote_instance is None:
            self._add_broken_record(
                code=self.ERROR_BROKEN_IMPORT_PROCESS,
                message="Remote instance missing after processing",
                data=instance.data,
                context={"sku": instance.data.get("sku", local_sku)},
            )
            return None

        self.update_remote_product(
            import_instance=instance,
            spu_payload=spu_payload,
            skc_payload=skc_payload,
            sku_payload=sku_payload,
            is_variation=is_variation,
        )

        if self.sales_channel.sync_contents and not is_variation:
            self.handle_translations(import_instance=instance)
            self.handle_images(import_instance=instance)

        if not is_configurable:
            if self.sales_channel.sync_ean_codes:
                self.handle_ean_code(import_instance=instance)
            if self.sales_channel.sync_contents and is_variation:
                self.handle_translations(import_instance=instance)
                self.handle_images(import_instance=instance)
            if self.sales_channel.sync_prices:
                self.handle_prices(import_instance=instance)

        self.handle_attributes(import_instance=instance)

        if parent_sku and is_variation:
            self.handle_variations(
                import_instance=instance,
                parent_sku=parent_sku,
                parent_remote=parent_remote,
            )

        if not is_variation:
            self.handle_sales_channels_views(
                import_instance=instance,
                structured_data=instance.data,
                spu_payload=spu_payload,
            )

        return instance


class SheinProductsAsyncImportProcessor(AsyncProductImportMixin, SheinProductsImportProcessor):
    """Async variant of the Shein product import processor."""

    def dispatch_task(
        self,
        *,
        data: dict[str, Any],
        is_last: bool = False,
        updated_with: int | None = None,
    ) -> None:
        from sales_channels.integrations.shein.tasks import shein_product_import_item_task

        task_kwargs = {
            "import_process_id": self.import_process.id,
            "sales_channel_id": self.sales_channel.id,
            "data": data,
            "is_last": is_last,
            "updated_with": updated_with,
        }

        sku = data.get("sku") if isinstance(data, dict) else None
        shein_product_import_item_task(**task_kwargs)

    def run(self) -> None:
        self.prepare_import_process()
        if hasattr(self, "disable_inspector_signals"):
            self.disable_inspector_signals()
        self.strat_process()

        self.import_process.total_records = self.get_total_instances()
        self.import_process.processed_records = 0
        self.import_process.percentage = 0
        self.import_process.save(update_fields=["total_records", "processed_records", "percentage", "status"])
        self.total_import_instances_cnt = self.import_process.total_records
        self.set_threshold_chunk()

        self.skipped_inspector_sku = getattr(self, "skipped_inspector_sku", set())

        serialized: dict[str, Any] | None = None
        idx = 0

        for idx, item in enumerate(self.get_products_data(), start=1):
            update_delta = None
            if idx % self._threshold_chunk == 0:
                update_delta = math.floor((idx / self.total_import_instances_cnt) * 100)

            serialized = serialize_listing_item(item)
            sku = serialized.get("sku")
            if sku:
                self.skipped_inspector_sku.add(sku)
            self.dispatch_task(data=serialized, is_last=False, updated_with=update_delta)

        if serialized:
            update_delta = idx % self._threshold_chunk if idx % self._threshold_chunk != 0 else None
            self.dispatch_task(data=serialized, is_last=True, updated_with=update_delta)

        if hasattr(self, "refresh_inspector_status"):
            self.refresh_inspector_status()


class SheinProductItemFactory(SheinProductsImportProcessor):
    """Factory that will handle the import of a single Shein product payload."""

    def __init__(
        self,
        *,
        product_data: dict[str, Any],
        import_process,
        sales_channel,
        is_last: bool = False,
        updated_with: int | None = None,
    ) -> None:
        super().__init__(import_process=import_process, sales_channel=sales_channel)

        self.product_data = product_data
        self.is_last = is_last
        self.updated_with = updated_with

    def run(self) -> None:
        self.disable_inspector_signals()

        try:
            self.process_product_item(product_data=self.product_data)
        except Exception as exc:
            self._add_broken_record(
                code="UNKNOWN_ERROR",
                message="Unexpected error while processing product",
                data=self.product_data,
                exc=exc,
            )
        finally:
            self.refresh_inspector_status(run_inspection=False)

        if self.updated_with:
            increment_processed_records(self.import_process.id, delta=self.updated_with)
        if self.is_last:
            self.mark_success()
            self.process_completed()
