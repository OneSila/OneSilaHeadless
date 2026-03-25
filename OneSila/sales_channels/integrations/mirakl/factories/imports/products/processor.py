from __future__ import annotations

import hashlib
import math
import time
from typing import Any, Iterator

from django.db import IntegrityError
from django.utils.text import slugify

from imports_exports.factories.mixins import UpdateOnlyInstanceNotFound
from imports_exports.factories.products import ImportProductInstance
from products.models import Product
from sales_channels.factories.imports.imports import SalesChannelImportMixin
from sales_channels.integrations.mirakl.factories.imports.products.client import MiraklProductsImportClient
from sales_channels.integrations.mirakl.factories.imports.products.reverse_mapper import MiraklReverseProductMapper
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import (
    MiraklCategory,
    MiraklEanCode,
    MiraklPrice,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklSalesChannelView,
)
from sales_channels.models import SalesChannelViewAssign


class MiraklProductsImportProcessor(GetMiraklAPIMixin, SalesChannelImportMixin):
    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    remote_ean_code_class = MiraklEanCode
    remote_product_content_class = MiraklProductContent
    remote_price_class = MiraklPrice

    page_interval_seconds = 5

    def __init__(self, *, import_process, sales_channel, language=None):
        super().__init__(import_process=import_process, sales_channel=sales_channel, language=language)
        self.client = MiraklProductsImportClient(sales_channel=sales_channel)
        self.mapper = MiraklReverseProductMapper(sales_channel=sales_channel)
        self._prepared_groups: list[dict[str, Any]] | None = None
        self._offers_total_count = 0
        self._p11_products_by_reference: dict[tuple[str, str], dict[str, Any]] = {}
        self._p11_products_by_sku: dict[str, dict[str, Any]] = {}
        self._p31_products_by_reference: dict[tuple[str, str], dict[str, Any]] = {}
        self._p31_products_by_sku: dict[str, dict[str, Any]] = {}

    def prepare_import_process(self):
        super().prepare_import_process()
        self.import_process.status = self.import_process.STATUS_PROCESSING
        self.import_process.name = f"Mirakl products import - {self.sales_channel.hostname} [OF21]"
        self.import_process.save(update_fields=["status", "name"])

    def get_properties_data(self):
        return []

    def get_select_values_data(self):
        return []

    def get_rules_data(self):
        return []

    def get_total_instances(self):
        self._load_groups()
        self.import_process.total_records = self._offers_total_count
        self.import_process.processed_records = 0
        self.import_process.save(update_fields=["total_records", "processed_records"])
        return self._offers_total_count

    def get_products_data(self) -> Iterator[dict[str, Any]]:
        yield from self._load_groups()

    def import_products_process(self):
        for payload in self.get_products_data():
            offer_count = len(payload.get("offers") or [])
            self._process_group_payload(payload=payload)
            self.import_process.processed_records = (self.import_process.processed_records or 0) + offer_count
            total_records = self.import_process.total_records or self.total_import_instances_cnt or 0
            if total_records > 0:
                new_percentage = math.floor((self.import_process.processed_records / total_records) * 100)
                if self.import_process.processed_records > 0:
                    new_percentage = max(1, new_percentage)
                self.current_percent = min(new_percentage, 99)
                self.import_process.percentage = self.current_percent
                self.import_process.save(update_fields=["processed_records", "percentage"])
            else:
                self.import_process.save(update_fields=["processed_records"])
            self.total_imported_instances = self.import_process.processed_records or 0

    def _process_group_payload(self, *, payload: dict[str, Any]) -> None:
        offer_entries = payload.get("offers") or []
        if not offer_entries:
            return

        parent_local_product = None
        parent_remote_product = None
        if len(offer_entries) > 1:
            parent_local_product, parent_remote_product = self._ensure_synthetic_parent(payload=payload)

        for offer_entry in offer_entries:
            self._process_offer_entry(
                payload=payload,
                offer_entry=offer_entry,
                parent_local_product=parent_local_product,
                parent_remote_product=parent_remote_product,
            )

        if parent_local_product is not None and parent_remote_product is not None:
            self._update_view_assigns_for_channels(
                product=parent_local_product,
                remote_product=parent_remote_product,
                channel_codes=self._collect_group_channel_codes(payload=payload),
            )

    def _process_offer_entry(
        self,
        *,
        payload: dict[str, Any],
        offer_entry: dict[str, Any],
        parent_local_product: Product | None,
        parent_remote_product: MiraklProduct | None,
    ) -> None:
        mapper_payload = {
            "offer": offer_entry.get("offer") or {},
            "p11_product": offer_entry.get("p11_product") or {},
            "p31_product": self._get_p31_product(offer=offer_entry.get("offer") or {}),
        }
        structured, structured_log, product_rule = self.mapper.build(payload=mapper_payload)
        if parent_local_product is not None:
            structured["configurable_parent_sku"] = parent_local_product.sku

        remote_sku = self._normalize_remote_value(structured.get("__mirakl_remote_sku"))
        remote_id = self._normalize_remote_value(structured.get("__mirakl_remote_id"))
        local_product = self._find_local_product(sku=structured.get("sku") or "")
        existing_remote_product = self._find_existing_remote_product(
            local_product=local_product,
            remote_sku=remote_sku,
            remote_parent_product=parent_remote_product,
        )
        import_instance = ImportProductInstance(
            structured,
            import_process=self.import_process,
            rule=product_rule,
            sales_channel=self.sales_channel,
            instance=getattr(existing_remote_product, "local_instance", None) or local_product,
        )

        try:
            import_instance.process()
        except UpdateOnlyInstanceNotFound as exc:
            self._handle_product_error(
                code="UPDATE_ONLY_NOT_FOUND",
                message="Mirakl product skipped because update_only is enabled and no local product exists.",
                payload=mapper_payload,
                sku=structured["sku"],
                exc=exc,
            )
            return
        except IntegrityError as exc:
            self._handle_product_error(
                code="BROKEN_IMPORT_PROCESS",
                message="Mirakl product import failed during local import processing.",
                payload=mapper_payload,
                sku=structured["sku"],
                exc=exc,
            )
            return
        except Exception as exc:
            self._handle_product_error(
                code="BROKEN_IMPORT_PROCESS",
                message="Mirakl product import failed.",
                payload=mapper_payload,
                sku=structured["sku"],
                exc=exc,
            )
            return

        remote_product = self._upsert_remote_product(
            existing_remote_product=existing_remote_product,
            local_product=import_instance.instance,
            remote_sku=remote_sku,
            remote_id=remote_id,
            parent_remote_product=parent_remote_product,
            structured=structured,
            mapper_payload=mapper_payload,
            group_hash=payload["group_hash"],
        )
        import_instance.set_remote_instance(remote_product)

        self._update_product_category(import_instance=import_instance, mapper_payload=mapper_payload)
        self._update_content_mirror(import_instance=import_instance)
        self._update_price_mirror(import_instance=import_instance)
        self._update_ean_mirrors(import_instance=import_instance, mapper_payload=mapper_payload)
        if parent_local_product is None:
            self._update_view_assigns_for_channels(
                product=import_instance.instance,
                remote_product=remote_product,
                channel_codes=self._collect_offer_channel_codes(offer=mapper_payload["offer"]),
            )
        else:
            self._clear_view_assigns(product=import_instance.instance)
        self.create_log_instance(import_instance=import_instance, structured_data=structured_log)

    def _ensure_synthetic_parent(self, *, payload: dict[str, Any]) -> tuple[Product, MiraklProduct]:
        existing_parent_remote = (
            MiraklProduct.objects.filter(
                sales_channel=self.sales_channel,
                raw_data__configurable_group_hash=payload["group_hash"],
                raw_data__synthetic_configurable=True,
            )
            .select_related("local_instance")
            .order_by("id")
            .first()
        )
        existing_parent_local = getattr(existing_parent_remote, "local_instance", None)
        representative_mapper_payload, representative_structured = self._get_representative_parent_data(payload=payload)
        parent_payload = self._build_synthetic_parent_payload(
            payload=payload,
            representative_structured=representative_structured,
        )
        import_instance = ImportProductInstance(
            parent_payload,
            import_process=self.import_process,
            sales_channel=self.sales_channel,
            instance=existing_parent_local,
        )
        import_instance.process()
        remote_product = self._upsert_remote_product(
            existing_remote_product=existing_parent_remote,
            local_product=import_instance.instance,
            remote_sku=None,
            remote_id=None,
            parent_remote_product=None,
            structured=parent_payload,
            mapper_payload={
                **representative_mapper_payload,
                "synthetic": True,
                "group_values": payload["group_values"],
            },
            group_hash=payload["group_hash"],
            is_variation=False,
            title=parent_payload.get("name") or "",
            brand=str(payload["group_values"].get("product_brand") or "").strip(),
        )
        import_instance.set_remote_instance(remote_product)
        self._update_product_category(
            import_instance=import_instance,
            mapper_payload={
                **representative_mapper_payload,
                "group_values": payload["group_values"],
            },
        )
        self._update_content_mirror(import_instance=import_instance)
        return import_instance.instance, remote_product

    def _build_synthetic_parent_payload(
        self,
        *,
        payload: dict[str, Any],
        representative_structured: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        group_values = payload["group_values"]
        title = str(group_values.get("product_title") or "").strip() or f"Mirakl Group {payload['group_hash'][:10]}"
        description = str(group_values.get("product_description") or "").strip()
        short_description = str(group_values.get("internal_description") or "").strip()
        parent_payload = {
            "name": title,
            "type": Product.CONFIGURABLE,
            "active": any(self._is_offer_active(offer=entry.get("offer") or {}) for entry in payload.get("offers") or []),
            "translations": [
                {
                    "language": self.language or self.sales_channel.multi_tenant_company.language,
                    "sales_channel": self.sales_channel,
                    "name": title,
                    "subtitle": "",
                    "description": description,
                    "short_description": short_description,
                    "url_key": slugify(title) or payload["group_hash"][:16],
                    "bullet_points": [],
                }
            ],
        }
        representative_structured = representative_structured or {}
        if representative_structured.get("images"):
            parent_payload["images"] = representative_structured["images"]
        if representative_structured.get("documents"):
            parent_payload["documents"] = representative_structured["documents"]
        return parent_payload

    def _get_representative_parent_data(self, *, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        fallback_mapper_payload = {
            "offer": {},
            "p11_product": {},
            "p31_product": {},
        }
        fallback_structured: dict[str, Any] = {}

        for offer_entry in payload.get("offers") or []:
            mapper_payload = {
                "offer": offer_entry.get("offer") or {},
                "p11_product": offer_entry.get("p11_product") or {},
                "p31_product": offer_entry.get("p31_product") or {},
            }
            structured, _, _ = self.mapper.build(payload=mapper_payload)
            if not fallback_structured:
                fallback_mapper_payload = mapper_payload
                fallback_structured = structured
            if structured.get("images") or structured.get("documents"):
                return mapper_payload, structured

        return fallback_mapper_payload, fallback_structured

    def _upsert_remote_product(
        self,
        *,
        existing_remote_product: MiraklProduct | None,
        local_product: Product,
        remote_sku: str | None,
        remote_id: str | None,
        parent_remote_product: MiraklProduct | None,
        structured: dict[str, Any],
        mapper_payload: dict[str, Any],
        group_hash: str,
        is_variation: bool | None = None,
        title: str | None = None,
        brand: str | None = None,
    ) -> MiraklProduct:
        remote_product = existing_remote_product
        if remote_product is None:
            remote_product = MiraklProduct.objects.create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=local_product,
                remote_sku=remote_sku,
                remote_id=remote_id,
                is_variation=bool(parent_remote_product) if is_variation is None else is_variation,
                remote_parent_product=parent_remote_product,
            )
        update_fields: list[str] = []
        for field_name, value in (
            ("local_instance", local_product),
            ("remote_sku", remote_sku),
            ("remote_id", remote_id),
            ("remote_parent_product", parent_remote_product),
            ("is_variation", bool(parent_remote_product) if is_variation is None else is_variation),
            ("product_id_type", self._resolve_product_id_type(mapper_payload=mapper_payload)),
            ("product_reference", self._resolve_product_reference(mapper_payload=mapper_payload)),
            ("title", title if title is not None else str(structured.get("name") or "")),
            (
                "brand",
                brand
                if brand is not None
                else str(
                    (mapper_payload.get("offer") or {}).get("product_brand")
                    or (mapper_payload.get("p11_product") or {}).get("product_brand")
                    or (mapper_payload.get("p31_product") or {}).get("product_brand")
                    or ""
                ),
            ),
            (
                "raw_data",
                {
                    "configurable_group_hash": group_hash,
                    "synthetic_configurable": bool(mapper_payload.get("synthetic")),
                    "offer": mapper_payload.get("offer") or {},
                    "p11_product": mapper_payload.get("p11_product") or {},
                    "p31_product": mapper_payload.get("p31_product") or {},
                    "group_values": mapper_payload.get("group_values") or {},
                },
            ),
            ("syncing_current_percentage", 100),
        ):
            if getattr(remote_product, field_name) != value:
                setattr(remote_product, field_name, value)
                update_fields.append(field_name)
        if update_fields:
            remote_product.save(update_fields=update_fields)
        return remote_product

    def _resolve_product_id_type(self, *, mapper_payload: dict[str, Any]) -> str:
        p11_product = mapper_payload.get("p11_product") or {}
        p31_product = mapper_payload.get("p31_product") or {}
        offer = mapper_payload.get("offer") or {}
        references = self._extract_references(mapper_payload=mapper_payload)
        primary_reference = references[0] if references else {}
        return str(
            p31_product.get("product_id_type")
            or p11_product.get("product_id_type")
            or p31_product.get("reference_type")
            or primary_reference.get("reference_type")
            or offer.get("product_id_type")
            or ""
        )

    def _resolve_product_reference(self, *, mapper_payload: dict[str, Any]) -> str:
        p11_product = mapper_payload.get("p11_product") or {}
        p31_product = mapper_payload.get("p31_product") or {}
        references = self._extract_references(mapper_payload=mapper_payload)
        primary_reference = references[0] if references else {}
        return str(
            p31_product.get("product_reference")
            or p31_product.get("product_id")
            or p11_product.get("product_reference")
            or primary_reference.get("reference")
            or ""
        )

    def _extract_references(self, *, mapper_payload: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("offer", "p11_product", "p31_product"):
            references = (mapper_payload.get(key) or {}).get("product_references") or []
            if isinstance(references, list) and references:
                return [reference for reference in references if isinstance(reference, dict)]
        return []

    def _update_content_mirror(self, *, import_instance: ImportProductInstance):
        translations = getattr(import_instance, "translations", []) or []
        if not translations:
            return
        mirror, _ = MiraklProductContent.objects.get_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=import_instance.remote_instance,
        )
        content_data: dict[str, Any] = {}
        for translation in translations:
            language = str(translation.get("language") or self.language or self.sales_channel.multi_tenant_company.language)
            content_data[language] = {
                "name": translation.get("name") or "",
                "subtitle": translation.get("subtitle") or "",
                "description": translation.get("description") or "",
                "short_description": translation.get("short_description") or "",
                "url_key": translation.get("url_key") or "",
                "bullet_points": translation.get("bullet_points") or [],
            }
        mirror.content_data = content_data
        mirror.save()

    def _update_product_category(self, *, import_instance: ImportProductInstance, mapper_payload: dict[str, Any]) -> None:
        merged_fields = self._merge_product_data(
            offer=mapper_payload.get("offer") or {},
            p11_product=mapper_payload.get("p11_product") or {},
            p31_product=mapper_payload.get("p31_product") or {},
        )
        category_code = str(merged_fields.get("category_code") or "").strip()
        if not category_code or import_instance.instance is None:
            return
        if not MiraklCategory.objects.filter(sales_channel=self.sales_channel, remote_id=category_code).exists():
            return

        MiraklProductCategory.objects.update_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=import_instance.instance,
            require_view=False,
            defaults={
                "remote_id": category_code,
                "view": None,
            },
        )

    def _update_price_mirror(self, *, import_instance: ImportProductInstance):
        prices = getattr(import_instance, "prices", []) or []
        offer_id = str(import_instance.data.get("__mirakl_offer_id") or "").strip()
        if not prices and not offer_id:
            return

        mirror, _ = MiraklPrice.objects.get_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=import_instance.remote_instance,
        )
        update_fields: list[str] = []
        if offer_id and mirror.remote_id != offer_id:
            mirror.remote_id = offer_id
            update_fields.append("remote_id")

        price_data: dict[str, Any] = {}
        for entry in prices:
            currency = str(entry.get("currency") or "").strip()
            if not currency:
                continue
            payload: dict[str, Any] = {}
            if entry.get("rrp") not in (None, ""):
                payload["price"] = float(entry["rrp"])
            if entry.get("price") not in (None, ""):
                payload["discount_price"] = float(entry["price"])
                if "price" not in payload:
                    payload["price"] = float(entry["price"])
            if payload:
                price_data[currency] = payload
        if price_data and mirror.price_data != price_data:
            mirror.price_data = price_data
            update_fields.append("price_data")
        if update_fields:
            mirror.save(update_fields=update_fields)

    def _update_ean_mirrors(self, *, import_instance: ImportProductInstance, mapper_payload: dict[str, Any]):
        for reference in self._extract_references(mapper_payload=mapper_payload):
            reference_type = str(reference.get("reference_type") or "").upper()
            if reference_type != "EAN" and not reference_type.startswith("EAN-"):
                continue
            ean_code = str(reference.get("reference") or "").strip()
            if not ean_code:
                continue
            MiraklEanCode.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=import_instance.remote_instance,
                ean_code=ean_code[:14],
            )

    def _update_view_assigns_for_channels(
        self,
        *,
        product: Product,
        remote_product: MiraklProduct,
        channel_codes: set[str],
    ) -> None:
        views_queryset = MiraklSalesChannelView.objects.filter(sales_channel=self.sales_channel)
        if channel_codes:
            views_queryset = views_queryset.filter(remote_id__in=channel_codes)
        for view in views_queryset:
            SalesChannelViewAssign.objects.update_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                sales_channel_view=view,
                product=product,
                defaults={"remote_product": remote_product},
            )

    def _clear_view_assigns(self, *, product: Product) -> None:
        SalesChannelViewAssign.objects.filter(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            product=product,
        ).delete()

    def _load_groups(self) -> list[dict[str, Any]]:
        if self._prepared_groups is not None:
            return self._prepared_groups

        page_size = min(100, self.client.default_page_size)
        offset = 0
        total_count: int | None = None
        offers_payloads: list[dict[str, Any]] = []
        product_references: list[tuple[str, str]] = []
        grouped_payloads: dict[str, dict[str, Any]] = {}

        while True:
            page_payload = self.client.get_offers_page(offset=offset, max_items=page_size)
            offers = page_payload.get("offers") or []
            if total_count is None and isinstance(page_payload.get("total_count"), int):
                total_count = max(page_payload["total_count"], 0)
            for offer in offers:
                offers_payloads.append(offer)
                product_references.extend(self._extract_product_references(offer=offer))

            offset += len(offers)
            reached_total = isinstance(total_count, int) and offset >= total_count
            has_more_pages = isinstance(total_count, int) and offset < total_count
            if not offers or reached_total or not has_more_pages:
                break
            time.sleep(self.page_interval_seconds)

        self._populate_product_enrichment_indexes(product_references=product_references)
        for offer in offers_payloads:
            self._append_offer_to_group(
                groups=grouped_payloads,
                offer=offer,
                p11_product=self._get_p11_product(offer=offer),
                p31_product=self._get_p31_product(offer=offer),
            )

        self._offers_total_count = total_count if isinstance(total_count, int) else offset
        self._prepared_groups = list(grouped_payloads.values())
        return self._prepared_groups

    def _append_offer_to_group(
        self,
        *,
        groups: dict[str, dict[str, Any]],
        offer: dict[str, Any],
        p11_product: dict[str, Any] | None = None,
        p31_product: dict[str, Any] | None = None,
    ) -> None:
        group_values = self._build_group_values(
            offer=offer,
            p11_product=p11_product or {},
            p31_product=p31_product or {},
        )
        group_hash = hashlib.sha256(
            "||".join(
                [
                    group_values["product_title"],
                    group_values["product_brand"],
                    group_values["product_description"],
                    group_values["internal_description"],
                    group_values["category_code"],
                ]
            ).encode("utf-8")
        ).hexdigest()
        group = groups.setdefault(
            group_hash,
            {
                "group_hash": group_hash,
                "group_values": group_values,
                "offers": [],
            },
        )
        group["offers"].append(
            {
                "offer": offer,
                "p11_product": p11_product or {},
                "p31_product": p31_product or {},
            }
        )

    def _build_group_values(
        self,
        *,
        offer: dict[str, Any],
        p11_product: dict[str, Any],
        p31_product: dict[str, Any],
    ) -> dict[str, str]:
        merged_fields = self._merge_product_data(
            offer=offer,
            p11_product=p11_product,
            p31_product=p31_product,
        )
        return {
            "product_title": self._normalize_group_value(merged_fields.get("product_title")),
            "product_brand": self._normalize_group_value(merged_fields.get("product_brand")),
            "product_description": self._normalize_group_value(merged_fields.get("product_description")),
            "internal_description": self._normalize_group_value(offer.get("internal_description")),
            "category_code": self._normalize_group_value(merged_fields.get("category_code")),
        }

    def _normalize_group_value(self, value: Any) -> str:
        return str(value or "").strip()

    def _extract_product_references(self, *, offer: dict[str, Any]) -> list[tuple[str, str]]:
        references = offer.get("product_references") or []
        if not isinstance(references, list):
            return []
        extracted_references: list[tuple[str, str]] = []
        for reference in references:
            if not isinstance(reference, dict):
                continue
            reference_type = str(reference.get("reference_type") or "").upper()
            reference_value = str(reference.get("reference") or "").strip()
            if not reference_type or not reference_value:
                continue
            if reference_type in {"SHOP_SKU", "SKU"}:
                continue
            extracted_references.append((reference_type, reference_value))
        return extracted_references

    def _populate_product_enrichment_indexes(self, *, product_references: list[tuple[str, str]]) -> None:
        self._p11_products_by_reference = {}
        self._p11_products_by_sku = {}
        self._p31_products_by_reference = {}
        self._p31_products_by_sku = {}

        for product in self.client.get_products_offers_by_references(product_references=product_references):
            product_sku = self._normalize_remote_value(product.get("product_sku"))
            if product_sku and product_sku not in self._p11_products_by_sku:
                self._p11_products_by_sku[product_sku] = product
            for reference_key in self._extract_reference_keys_from_product(product=product):
                self._p11_products_by_reference.setdefault(reference_key, product)

        for product in self.client.get_products_by_references(product_references=product_references):
            product_sku = self._normalize_remote_value(product.get("product_sku"))
            if product_sku and product_sku not in self._p31_products_by_sku:
                self._p31_products_by_sku[product_sku] = product
            reference_key = self._build_reference_key(
                reference_type=product.get("product_id_type"),
                reference=product.get("product_id"),
            )
            if reference_key is not None:
                self._p31_products_by_reference.setdefault(reference_key, product)

    def _get_p11_product(self, *, offer: dict[str, Any]) -> dict[str, Any] | None:
        for reference_key in self._extract_reference_keys_from_offer(offer=offer):
            if reference_key in self._p11_products_by_reference:
                return self._p11_products_by_reference[reference_key]
        product_sku = self._normalize_remote_value(offer.get("product_sku"))
        if product_sku:
            return self._p11_products_by_sku.get(product_sku)
        return None

    def _get_p31_product(self, *, offer: dict[str, Any]) -> dict[str, Any] | None:
        for reference_key in self._extract_reference_keys_from_offer(offer=offer):
            if reference_key in self._p31_products_by_reference:
                return self._p31_products_by_reference[reference_key]
        product_sku = self._normalize_remote_value(offer.get("product_sku"))
        if product_sku:
            return self._p31_products_by_sku.get(product_sku)
        return None

    def _extract_reference_keys_from_offer(self, *, offer: dict[str, Any]) -> list[tuple[str, str]]:
        return [
            reference_key
            for reference_type, reference in self._extract_product_references(offer=offer)
            if (reference_key := self._build_reference_key(reference_type=reference_type, reference=reference)) is not None
        ]

    def _extract_reference_keys_from_product(self, *, product: dict[str, Any]) -> list[tuple[str, str]]:
        references = product.get("product_references") or []
        if not isinstance(references, list):
            return []

        extracted_keys: list[tuple[str, str]] = []
        for reference in references:
            if not isinstance(reference, dict):
                continue
            reference_key = self._build_reference_key(
                reference_type=reference.get("reference_type"),
                reference=reference.get("reference"),
            )
            if reference_key is not None:
                extracted_keys.append(reference_key)
        return extracted_keys

    def _build_reference_key(self, *, reference_type: Any, reference: Any) -> tuple[str, str] | None:
        normalized_reference_type = str(reference_type or "").strip().upper()
        normalized_reference = str(reference or "").strip()
        if not normalized_reference_type or not normalized_reference:
            return None
        if normalized_reference_type in {"SHOP_SKU", "SKU"}:
            return None
        return normalized_reference_type, normalized_reference

    def _merge_product_data(
        self,
        *,
        offer: dict[str, Any],
        p11_product: dict[str, Any],
        p31_product: dict[str, Any],
    ) -> dict[str, Any]:
        merged_fields = dict(offer)
        for source in (p11_product, p31_product):
            for key, value in source.items():
                if key not in merged_fields or merged_fields.get(key) in (None, "", [], {}):
                    merged_fields[key] = value
        return merged_fields

    def _find_local_product(self, *, sku: str) -> Product | None:
        normalized_sku = str(sku or "").strip()
        if not normalized_sku:
            return None
        return Product.objects.filter(
            sku=normalized_sku,
            multi_tenant_company=self.import_process.multi_tenant_company,
        ).first()

    def _find_existing_remote_product(
        self,
        *,
        local_product: Product | None,
        remote_sku: str | None,
        remote_parent_product: MiraklProduct | None,
    ) -> MiraklProduct | None:
        if remote_sku:
            remote_by_sku = (
                MiraklProduct.objects.filter(
                    sales_channel=self.sales_channel,
                    remote_sku=remote_sku,
                )
                .select_related("local_instance", "remote_parent_product")
                .order_by("id")
                .first()
            )
            if remote_by_sku is not None:
                return remote_by_sku

        if local_product is None:
            return None

        queryset = MiraklProduct.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=local_product,
        ).select_related("local_instance", "remote_parent_product")
        if remote_parent_product is not None:
            exact_match = queryset.filter(remote_parent_product=remote_parent_product).order_by("id").first()
            if exact_match is not None:
                return exact_match
        return queryset.order_by("id").first()

    def _collect_offer_channel_codes(self, *, offer: dict[str, Any]) -> set[str]:
        channel_codes: set[str] = set()
        channels = offer.get("channels") or []
        if isinstance(channels, str):
            channels = [part.strip() for part in channels.split(",") if part.strip()]
        for channel_code in channels:
            normalized = str(channel_code or "").strip()
            if normalized:
                channel_codes.add(normalized)
        return channel_codes

    def _collect_group_channel_codes(self, *, payload: dict[str, Any]) -> set[str]:
        channel_codes: set[str] = set()
        for offer_entry in payload.get("offers") or []:
            channel_codes.update(self._collect_offer_channel_codes(offer=offer_entry.get("offer") or {}))
        return channel_codes

    def _normalize_remote_value(self, value: Any) -> str | None:
        normalized = str(value or "").strip()
        return normalized or None

    def _is_offer_active(self, *, offer: dict[str, Any]) -> bool:
        deleted = offer.get("deleted")
        if deleted in (True, "true", "TRUE", 1, "1"):
            return False
        active = offer.get("active")
        return active in (True, "true", "TRUE", 1, "1", None, "")

    def _handle_product_error(
        self,
        *,
        code: str,
        message: str,
        payload: dict[str, Any],
        sku: str,
        exc: Exception | None = None,
    ) -> None:
        self._add_broken_record(
            code=code,
            message=message,
            data=payload,
            context={"sku": sku},
            exc=exc,
        )
        if not self.import_process.skip_broken_records:
            if exc is not None:
                raise exc
            raise ValueError(message)
