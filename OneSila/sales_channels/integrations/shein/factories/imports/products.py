"""Shein product import processors."""

from __future__ import annotations

import math
from collections.abc import Iterator, Mapping
from typing import Any

from django.db import IntegrityError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from core.mixins import TemporaryDisableInspectorSignalsMixin
from imports_exports.factories.imports import AsyncProductImportMixin
from imports_exports.factories.products import ImportProductInstance
from imports_exports.helpers import increment_processed_records
from products.product_types import CONFIGURABLE
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
    SheinDocument,
    SheinDocumentThroughProduct,
    SheinDocumentType,
    SheinEanCode,
    SheinImageProductAssociation,
    SheinProduct,
    SheinProductContent,
    SheinPrice,
    SheinProductType,
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

    remote_ean_code_class = SheinEanCode
    remote_product_content_class = SheinProductContent
    remote_imageproductassociation_class = SheinImageProductAssociation
    remote_documentproductassociation_class = SheinDocumentThroughProduct
    remote_document_class = SheinDocument
    remote_price_class = SheinPrice

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
        self._mapped_document_types_by_remote_id: dict[str, SheinDocumentType] | None = None

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
        spu_document_payloads = self._build_documents_for_spu(spu_name=spu_name)
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
            documents_payload=spu_document_payloads,
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
                documents_payload=spu_document_payloads,
            )

    def _get_mapped_document_types_by_remote_id(self) -> dict[str, SheinDocumentType]:
        if self._mapped_document_types_by_remote_id is not None:
            return self._mapped_document_types_by_remote_id

        queryset = (
            SheinDocumentType.objects.filter(
                sales_channel=self.sales_channel,
                multi_tenant_company=self.multi_tenant_company,
            )
            .exclude(local_instance__isnull=True)
            .select_related("local_instance")
        )
        mapped: dict[str, SheinDocumentType] = {}
        for remote_document_type in queryset:
            remote_id = str(remote_document_type.remote_id or "").strip()
            if not remote_id:
                continue
            mapped[remote_id] = remote_document_type

        self._mapped_document_types_by_remote_id = mapped
        return mapped

    def _build_documents_for_spu(self, *, spu_name: str) -> list[dict[str, Any]]:
        mapped_types = self._get_mapped_document_types_by_remote_id()
        if not mapped_types:
            return []

        try:
            certificate_records = self.get_certificate_rule_by_product_spu(spu_name=spu_name)
        except Exception as exc:
            self._add_broken_record(
                code=self.ERROR_INVALID_PRODUCT_DATA,
                message="Unable to fetch Shein certificate rules for SPU",
                data={"spu_name": spu_name},
                exc=exc,
            )
            return []

        documents: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str, str, str, str]] = set()

        for record in certificate_records:
            if not isinstance(record, Mapping):
                continue

            certificate_dimension = str(record.get("certificateDimension") or "").strip()
            if certificate_dimension and certificate_dimension != "1":
                continue

            certificate_type_id = str(record.get("certificateTypeId") or "").strip()
            if not certificate_type_id:
                continue

            remote_document_type = mapped_types.get(certificate_type_id)
            if remote_document_type is None or remote_document_type.local_instance is None:
                continue

            missing_status = bool(record.get("certificateMissStatus"))
            sources: list[Mapping[str, Any]] = []
            pool_list = record.get("certificatePoolList")
            if isinstance(pool_list, list):
                sources.extend(item for item in pool_list if isinstance(item, Mapping))
            other_source_list = record.get("otherSourceCertInfoList")
            if isinstance(other_source_list, list):
                sources.extend(item for item in other_source_list if isinstance(item, Mapping))

            for source in sources:
                certificate_pool_id = str(source.get("certificatePoolId") or "").strip()
                pqms_certificate_sn = str(source.get("pqmsCertificateSn") or "").strip()
                expire_time = source.get("expireTime")

                file_list = source.get("certificatePoolFileList")
                if not isinstance(file_list, list):
                    continue

                for file_payload in file_list:
                    if not isinstance(file_payload, Mapping):
                        continue

                    document_url = str(file_payload.get("certificateUrl") or "").strip()
                    if not document_url:
                        continue

                    remote_filename = str(file_payload.get("certificateUrlName") or "").strip()
                    dedupe_key = (
                        certificate_type_id,
                        certificate_pool_id,
                        pqms_certificate_sn,
                        document_url,
                        remote_filename,
                    )
                    if dedupe_key in seen_keys:
                        continue
                    seen_keys.add(dedupe_key)

                    document_payload: dict[str, Any] = {
                        "document_url": document_url,
                        "title": remote_filename or remote_document_type.name or remote_document_type.remote_id,
                        "document_type": remote_document_type.local_instance,
                        "document_language": self.multi_tenant_company.language,
                        "__shein_remote_document_type_id": str(remote_document_type.id),
                        "__shein_certificate_pool_id": certificate_pool_id,
                        "__shein_pqms_certificate_sn": pqms_certificate_sn,
                        "__shein_expire_time": str(expire_time or "").strip(),
                        "__shein_missing_status": missing_status,
                        "__shein_remote_url": document_url,
                        "__shein_remote_filename": remote_filename,
                    }
                    documents.append(document_payload)

        return documents

    @staticmethod
    def _parse_shein_expire_time(*, value) -> Any | None:
        expire_time_raw = str(value or "").strip()
        if not expire_time_raw:
            return None

        parsed = parse_datetime(expire_time_raw.replace(" ", "T"))
        if parsed is None:
            return None
        if timezone.is_naive(parsed):
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed

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
        documents_payload: list[dict[str, Any]] | None = None,
    ) -> ImportProductInstance | None:
        spu_name = self._extract_spu_name(payload=spu_payload)
        skc_name = self._extract_skc_name(payload=skc_payload)
        sku_code = self._extract_sku_code(payload=sku_payload)
        if is_configurable and not is_variation:
            skc_name = None
            sku_code = None

        local_sku = None
        if is_configurable and not is_variation:
            local_sku = spu_name
            if not local_sku:
                self._add_broken_record(
                    code=self.ERROR_INVALID_PRODUCT_DATA,
                    message="Unable to determine SKU for Shein product entry",
                    data={"spu_name": spu_name},
                )
                return None
        else:
            local_sku = self._resolve_local_sku(
                sku_payload=sku_payload,
                fallback_sku=parent_sku,
            )
            if not local_sku:
                self._add_broken_record(
                    code=self.ERROR_INVALID_PRODUCT_DATA,
                    message="Unable to determine SKU for Shein product entry",
                    data={"spu_name": spu_name},
                )
                return None

        remote_product = self._get_remote_product(
            sku=local_sku,
            spu_name=spu_name,
            sku_code=sku_code,
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

        if documents_payload and (is_variation or not is_configurable):
            structured["documents"] = documents_payload

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

        if structured.get("type") == CONFIGURABLE:
            instance.update_only = False
        else:
            instance.update_only = self.import_process.update_only

        mirror_defaults = {
            "is_variation": is_variation,
            "spu_name": spu_name,
            "skc_name": skc_name,
            "sku_code": sku_code,
        }
        if is_variation and parent_remote is not None:
            mirror_defaults["remote_parent_product"] = parent_remote

        instance.prepare_mirror_model_class(
            mirror_model_class=SheinProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults=mirror_defaults,
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
            spu_name=spu_name,
            skc_name=skc_name,
            sku_code=sku_code,
            is_variation=is_variation,
        )

        if self.sales_channel.sync_contents and not is_variation:
            self.handle_translations(import_instance=instance)
            self.handle_images(import_instance=instance)
        if not is_variation:
            self.handle_documents(import_instance=instance)

        if not is_configurable:
            if self.sales_channel.sync_ean_codes:
                self.handle_ean_code(import_instance=instance)
            if self.sales_channel.sync_contents and is_variation:
                self.handle_translations(import_instance=instance)
                self.handle_images(import_instance=instance)
            if is_variation:
                self.handle_documents(import_instance=instance)
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

    def handle_documents(self, *, import_instance: ImportProductInstance):
        if not hasattr(import_instance, "documents"):
            return

        for index, document_association in enumerate(import_instance.documents_associations_instances):
            media = getattr(document_association, "media", None)
            if media is None:
                continue

            document_payload = import_instance.documents[index] if index < len(import_instance.documents) else {}
            if not isinstance(document_payload, dict):
                continue

            remote_document_type_pk = str(document_payload.get("__shein_remote_document_type_id") or "").strip()
            if not remote_document_type_pk:
                continue

            remote_document_type = (
                SheinDocumentType.objects.filter(
                    id=remote_document_type_pk,
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.multi_tenant_company,
                )
                .select_related("local_instance")
                .first()
            )
            if remote_document_type is None:
                continue

            remote_document, _ = SheinDocument.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=media,
                remote_document_type=remote_document_type,
            )

            remote_document_update_fields: list[str] = []
            certificate_pool_id = str(document_payload.get("__shein_certificate_pool_id") or "").strip()
            remote_url = str(document_payload.get("__shein_remote_url") or "").strip()
            remote_filename = str(document_payload.get("__shein_remote_filename") or "").strip()

            if certificate_pool_id and remote_document.remote_id != certificate_pool_id:
                remote_document.remote_id = certificate_pool_id
                remote_document_update_fields.append("remote_id")
            if remote_url and remote_document.remote_url != remote_url:
                remote_document.remote_url = remote_url
                remote_document_update_fields.append("remote_url")
            if remote_filename and remote_document.remote_filename != remote_filename:
                remote_document.remote_filename = remote_filename
                remote_document_update_fields.append("remote_filename")

            if remote_document_update_fields:
                remote_document.save(update_fields=remote_document_update_fields)

            remote_association, _ = SheinDocumentThroughProduct.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=document_association,
                remote_product=import_instance.remote_instance,
                remote_document=remote_document,
                defaults={
                    "require_document": True,
                },
            )

            remote_association_update_fields: list[str] = []
            pqms_certificate_sn = str(document_payload.get("__shein_pqms_certificate_sn") or "").strip()
            expire_time = self._parse_shein_expire_time(value=document_payload.get("__shein_expire_time"))
            missing_status = bool(document_payload.get("__shein_missing_status"))

            if remote_association.require_document is False:
                remote_association.require_document = True
                remote_association_update_fields.append("require_document")
            if remote_association.remote_document_id != remote_document.id:
                remote_association.remote_document = remote_document
                remote_association_update_fields.append("remote_document")
            if pqms_certificate_sn and remote_association.remote_id != pqms_certificate_sn:
                remote_association.remote_id = pqms_certificate_sn
                remote_association_update_fields.append("remote_id")
            if remote_url and remote_association.remote_url != remote_url:
                remote_association.remote_url = remote_url
                remote_association_update_fields.append("remote_url")
            if remote_association.missing_status != missing_status:
                remote_association.missing_status = missing_status
                remote_association_update_fields.append("missing_status")
            if remote_association.expire_time != expire_time:
                remote_association.expire_time = expire_time
                remote_association_update_fields.append("expire_time")

            if remote_association_update_fields:
                remote_association.save(update_fields=remote_association_update_fields)


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
