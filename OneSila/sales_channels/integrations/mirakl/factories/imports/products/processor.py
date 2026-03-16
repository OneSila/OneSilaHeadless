from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Iterator

from django.db import IntegrityError

from imports_exports.factories.products import ImportProductInstance
from imports_exports.factories.mixins import UpdateOnlyInstanceNotFound
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

    initial_poll_delay_seconds = 30
    poll_interval_seconds = 60
    max_poll_attempts = 10

    def __init__(self, *, import_process, sales_channel, language=None):
        super().__init__(import_process=import_process, sales_channel=sales_channel, language=language)
        self.client = MiraklProductsImportClient(sales_channel=sales_channel)
        self.mapper = MiraklReverseProductMapper(sales_channel=sales_channel)
        self._prepared_products: list[dict[str, Any]] | None = None

    def prepare_import_process(self):
        super().prepare_import_process()
        self.import_process.status = self.import_process.STATUS_PROCESSING
        self.import_process.save(update_fields=["status"])
        self._initialize_total_records_from_account()

    def get_properties_data(self):
        return []

    def get_select_values_data(self):
        return []

    def get_rules_data(self):
        return []

    def get_total_instances(self):
        products = self._load_products()
        self.import_process.total_records = len(products)
        self.import_process.processed_records = 0
        self.import_process.save(update_fields=["total_records", "processed_records"])
        return len(products)

    def get_products_data(self) -> Iterator[dict[str, Any]]:
        yield from self._load_products()

    def import_products_process(self):
        for payload in self.get_products_data():
            self._process_single_payload(payload=payload)

    def _process_single_payload(self, *, payload: dict[str, Any]):
        structured, structured_log, product_rule = self.mapper.build(payload=payload)
        self._ensure_configurable_parent(payload=payload, structured=structured)
        remote_product = (
            MiraklProduct.objects.filter(
                sales_channel=self.sales_channel,
                remote_sku=structured["sku"],
            )
            .select_related("local_instance")
            .first()
        )
        local_product = getattr(remote_product, "local_instance", None)
        import_instance = ImportProductInstance(
            structured,
            import_process=self.import_process,
            rule=product_rule,
            sales_channel=self.sales_channel,
            instance=local_product,
        )
        import_instance.prepare_mirror_model_class(
            mirror_model_class=MiraklProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={"remote_sku": structured["sku"]},
        )

        try:
            import_instance.process()
        except UpdateOnlyInstanceNotFound as exc:
            self._handle_product_error(
                code="UPDATE_ONLY_NOT_FOUND",
                message="Mirakl product skipped because update_only is enabled and no local product exists.",
                payload=payload,
                sku=structured["sku"],
                exc=exc,
            )
            return
        except IntegrityError as exc:
            self._handle_product_error(
                code="BROKEN_IMPORT_PROCESS",
                message="Mirakl product import failed during local import processing.",
                payload=payload,
                sku=structured["sku"],
                exc=exc,
            )
            return
        except Exception as exc:
            self._handle_product_error(
                code="BROKEN_IMPORT_PROCESS",
                message="Mirakl product import failed.",
                payload=payload,
                sku=structured["sku"],
                exc=exc,
            )
            return

        if import_instance.remote_instance is None:
            self._handle_product_error(
                code="REMOTE_INSTANCE_MISSING",
                message="Mirakl product mirror was not created.",
                payload=payload,
                sku=structured["sku"],
            )
            return

        self._update_remote_product(remote_product=import_instance.remote_instance, payload=payload, structured=structured)
        self._update_product_category(import_instance=import_instance, payload=payload)
        self._update_content_mirror(import_instance=import_instance)
        self._update_price_mirror(import_instance=import_instance)
        self._update_ean_mirrors(import_instance=import_instance, payload=payload)
        self._update_view_assigns(import_instance=import_instance, payload=payload)
        self.create_log_instance(import_instance=import_instance, structured_data=structured_log)

        self.import_process.processed_records = (self.import_process.processed_records or 0) + 1
        self.import_process.save(update_fields=["processed_records"])
        self.update_percentage()

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
        return

    def _ensure_configurable_parent(self, *, payload: dict[str, Any], structured: dict[str, Any]) -> None:
        parent_sku = str(structured.get("configurable_parent_sku") or "").strip()
        child_sku = str(structured.get("sku") or "").strip()
        if not parent_sku or parent_sku == child_sku:
            return

        existing_parent = Product.objects.filter(
            sku=parent_sku,
            multi_tenant_company=self.import_process.multi_tenant_company,
        ).first()
        if existing_parent is not None:
            return

        parent_payload = {
            "sku": parent_sku,
            "name": parent_sku,
            "type": Product.CONFIGURABLE,
            "active": True,
            "__mirakl_export_rows": payload.get("export_rows") or [],
            "translations": [
                {
                    "language": self.language or self.sales_channel.multi_tenant_company.language,
                    "sales_channel": self.sales_channel,
                    "name": parent_sku,
                    "short_description": "",
                    "description": "",
                    "url_key": parent_sku.lower(),
                    "bullet_points": [],
                }
            ],
        }
        parent_import = ImportProductInstance(
            parent_payload,
            import_process=self.import_process,
            sales_channel=self.sales_channel,
        )
        parent_import.prepare_mirror_model_class(
            mirror_model_class=MiraklProduct,
            sales_channel=self.sales_channel,
            mirror_model_map={"local_instance": "*"},
            mirror_model_defaults={"remote_sku": parent_sku},
        )
        parent_import.process()
        if parent_import.remote_instance is not None:
            parent_import.remote_instance.title = parent_sku
            parent_import.remote_instance.raw_data = {
                "placeholder_configurable": True,
                "source_child_sku": child_sku,
            }
            parent_import.remote_instance.syncing_current_percentage = 100
            parent_import.remote_instance.save(
                update_fields=["title", "raw_data", "syncing_current_percentage"]
            )
            self._update_content_mirror(import_instance=parent_import)
            self._update_view_assigns(import_instance=parent_import, payload=payload)

    def _update_remote_product(self, *, remote_product: MiraklProduct, payload: dict[str, Any], structured: dict[str, Any]):
        product_data = payload.get("product") or {}
        references = [item for item in product_data.get("product_references") or [] if isinstance(item, dict)]
        primary_reference = references[0] if references else {}
        remote_product.product_id_type = str(
            product_data.get("product_id_type")
            or primary_reference.get("reference_type")
            or ""
        )
        remote_product.product_reference = str(
            product_data.get("product_id")
            or primary_reference.get("reference")
            or ""
        )
        remote_product.title = structured.get("name") or ""
        remote_product.raw_data = {
            "product": product_data,
            "export_rows": payload.get("export_rows") or [],
            "matched_offers": payload.get("matched_offers") or [],
        }
        remote_product.syncing_current_percentage = 100
        remote_product.save(
            update_fields=[
                "product_id_type",
                "product_reference",
                "title",
                "raw_data",
                "syncing_current_percentage",
            ]
        )

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

    def _update_product_category(self, *, import_instance: ImportProductInstance, payload: dict[str, Any]) -> None:
        product_data = payload.get("product") or {}
        category_code = str(product_data.get("category_code") or "").strip()
        if not category_code:
            return
        if import_instance.instance is None:
            return
        if not MiraklCategory.objects.filter(
            sales_channel=self.sales_channel,
            remote_id=category_code,
        ).exists():
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
        export_rows = import_instance.data.get("__mirakl_export_rows") or []
        offer_id = ""
        for row in export_rows:
            offer_id = str(row.get("offer_id") or row.get("offer-id") or "").strip()
            if offer_id:
                break

        if not prices and not offer_id:
            return
        mirror, _ = MiraklPrice.objects.get_or_create(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=import_instance.remote_instance,
        )
        if offer_id:
            mirror.remote_id = offer_id
        price_data: dict[str, Any] = {}
        for entry in prices:
            currency = str(entry.get("currency") or "").strip()
            if not currency:
                continue
            current_price = entry.get("price")
            original_price = entry.get("rrp")
            payload: dict[str, Any] = {}
            if original_price not in (None, ""):
                payload["price"] = float(original_price)
            if current_price not in (None, ""):
                payload["discount_price"] = float(current_price)
                if "price" not in payload:
                    payload["price"] = float(current_price)
            if payload:
                price_data[currency] = payload
        if price_data:
            mirror.price_data = price_data
        update_fields = ["remote_id"] if offer_id else []
        if price_data:
            update_fields.append("price_data")
        mirror.save(update_fields=update_fields or None)

    def _update_ean_mirrors(self, *, import_instance: ImportProductInstance, payload: dict[str, Any]):
        product_data = payload.get("product") or {}
        references = [item for item in product_data.get("product_references") or [] if isinstance(item, dict)]
        for reference in references:
            if str(reference.get("reference_type") or "").upper() != "EAN":
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

    def _update_view_assigns(self, *, import_instance: ImportProductInstance, payload: dict[str, Any]):
        channel_codes: set[str] = set()
        for row in payload.get("export_rows") or []:
            channels = row.get("channels") or []
            if isinstance(channels, str):
                channels = [part.strip() for part in channels.split(",") if part.strip()]
            channel_codes.update(str(code).strip() for code in channels if str(code).strip())

        views_queryset = MiraklSalesChannelView.objects.filter(sales_channel=self.sales_channel)
        if channel_codes:
            views_queryset = views_queryset.filter(remote_id__in=channel_codes)
        views = list(views_queryset)
        for view in views:
            SalesChannelViewAssign.objects.get_or_create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                sales_channel_view=view,
                product=import_instance.instance,
                remote_product=import_instance.remote_instance,
            )

    def _load_products(self) -> list[dict[str, Any]]:
        if self._prepared_products is None:
            export_payload = self._run_offer_export()
            product_payloads = self._hydrate_products(export_payload=export_payload)
            self._prepared_products = product_payloads
        return self._prepared_products

    def _initialize_total_records_from_account(self) -> None:
        account_info = self.client.get_account_info()
        offers_count = account_info.get("offers_count")
        if not isinstance(offers_count, int):
            return
        if offers_count < 0:
            return
        self.import_process.total_records = offers_count
        self.import_process.processed_records = 0
        self.import_process.save(update_fields=["total_records", "processed_records"])

    def _run_offer_export(self) -> dict[str, Any]:
        tracking_id = str(getattr(self.import_process, "tracking_id", "") or "").strip()
        if not tracking_id:
            export_response = self.client.start_full_offer_export()
            tracking_id = str(export_response.get("tracking_id") or "").strip()
            self.import_process.tracking_id = tracking_id
        else:
            export_response = {"tracking_id": tracking_id, "reused": True}
        if not tracking_id:
            raise ValueError("Mirakl OF52 response did not include a tracking_id.")

        self.import_process.name = f"Mirakl products import - {self.sales_channel.hostname} [{tracking_id}]"
        update_fields = ["name"]
        if "tracking_id" not in update_fields and getattr(self.import_process, "tracking_id", None) == tracking_id:
            update_fields.append("tracking_id")
        self.import_process.save(update_fields=update_fields)
        time.sleep(self.initial_poll_delay_seconds)
        last_status_payload: dict[str, Any] = {}
        for attempt in range(self.max_poll_attempts):
            last_status_payload = self.client.get_offer_export_status(tracking_id=tracking_id)
            status = str(last_status_payload.get("status") or "").upper()
            if status == "COMPLETED":
                urls = [url for url in last_status_payload.get("urls") or [] if isinstance(url, str) and url]
                rows: list[dict[str, Any]] = []
                for url in urls:
                    rows.extend(self.client.download_json_chunk(url=url))
                return {
                    "tracking_id": tracking_id,
                    "status_payload": last_status_payload,
                    "rows": rows,
                }
            if status == "FAILED":
                error_payload = last_status_payload.get("error") or last_status_payload
                raise ValueError(f"Mirakl OF53 failed: {error_payload}")
            if attempt < self.max_poll_attempts - 1:
                time.sleep(self.poll_interval_seconds)
        raise ValueError(f"Mirakl OF53 polling timed out for tracking_id={tracking_id}")

    def _hydrate_products(self, *, export_payload: dict[str, Any]) -> list[dict[str, Any]]:
        rows = [row for row in export_payload.get("rows") or [] if isinstance(row, dict)]
        rows_by_sku: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            sku = str(row.get("product_sku") or row.get("product-sku") or "").strip()
            if sku:
                rows_by_sku[sku].append(row)

        products_by_sku: dict[str, dict[str, Any]] = {}
        sku_list = list(rows_by_sku.keys())
        for start in range(0, len(sku_list), 100):
            batch = sku_list[start:start + 100]
            for product in self.client.get_products_offers(product_ids=batch):
                sku = str(product.get("product_sku") or "").strip()
                if sku:
                    products_by_sku[sku] = product

        hydrated: list[dict[str, Any]] = []
        for sku, export_rows in rows_by_sku.items():
            product_payload = products_by_sku.get(sku)
            if product_payload is None:
                self._add_broken_record(
                    code="P11_PRODUCT_MISSING",
                    message="Mirakl P11 did not return a product for an exported SKU.",
                    data={"sku": sku, "export_rows": export_rows},
                )
                continue
            matched_offers = self._match_p11_offers(product_payload=product_payload, export_rows=export_rows)
            hydrated.append(
                {
                    "product": product_payload,
                    "export_rows": export_rows,
                    "matched_offers": matched_offers,
                }
            )
        return hydrated

    def _match_p11_offers(self, *, product_payload: dict[str, Any], export_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        offer_ids = {
            str(row.get("offer_id") or row.get("offer-id") or "").strip()
            for row in export_rows
            if (row.get("offer_id") or row.get("offer-id")) not in (None, "")
        }
        shop_skus = {
            str(row.get("shop_sku") or row.get("shop-sku") or "").strip()
            for row in export_rows
            if (row.get("shop_sku") or row.get("shop-sku")) not in (None, "")
        }
        matched: list[dict[str, Any]] = []
        for offer in product_payload.get("offers") or []:
            if not isinstance(offer, dict):
                continue
            offer_id = str(offer.get("offer_id") or "").strip()
            shop_sku = str(offer.get("shop_sku") or "").strip()
            if offer_id and offer_id in offer_ids:
                matched.append(offer)
                continue
            if shop_sku and shop_sku in shop_skus:
                matched.append(offer)
        return matched
