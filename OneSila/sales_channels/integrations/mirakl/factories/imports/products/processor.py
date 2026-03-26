from __future__ import annotations

from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction

from core.mixins import TemporaryDisableInspectorSignalsMixin
from core.helpers import clean_json_data
from imports_exports.factories.products import ImportProductInstance
from media.models import MediaProductThrough
from products.models import ConfigurableVariation, Product
from sales_channels.exceptions import (
    MiraklImportConfigurableConflictError,
    MiraklImportInvalidFileLayoutError,
    MiraklImportInvalidFileTypeError,
    MiraklImportInvalidRowError,
    MiraklImportMissingFilesError,
)
from sales_channels.factories.imports.imports import SalesChannelImportMixin
from sales_channels.integrations.mirakl.factories.imports.products.reverse_mapper import (
    MiraklMappedRow,
    MiraklReverseProductMapper,
)
from sales_channels.integrations.mirakl.factories.imports.products.workbook import (
    MiraklImportErrorRow,
    MiraklImportRow,
    MiraklWorkbookParser,
)
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import (
    MiraklEanCode,
    MiraklPrice,
    MiraklProduct,
    MiraklProductCategory,
    MiraklProductContent,
    MiraklProductIssue,
    MiraklProperty,
    MiraklSalesChannelView,
)
from sales_channels.models import ImportProduct, RemoteImageProductAssociation, SalesChannelViewAssign
from sales_channels.models.products import RemoteProductConfigurator


class MiraklProductsImportProcessor(
    TemporaryDisableInspectorSignalsMixin,
    GetMiraklAPIMixin,
    SalesChannelImportMixin,
):
    import_properties = False
    import_select_values = False
    import_rules = False
    import_products = True

    ERROR_DUPLICATE_OFFER_SHOP_SKU = "DUPLICATE_OFFER_SHOP_SKU"
    ERROR_INVALID_ROW = "INVALID_ROW"
    ERROR_INVALID_CATEGORY_ASSIGNMENT = "INVALID_CATEGORY_ASSIGNMENT"
    ISSUE_SOURCE_ERROR_DETAILS = "xlsx_error_details"

    remote_ean_code_class = MiraklEanCode
    remote_product_content_class = MiraklProductContent
    remote_imageproductassociation_class = RemoteImageProductAssociation
    remote_price_class = MiraklPrice

    def __init__(self, *, import_process, sales_channel, language=None):
        super().__init__(
            import_process=import_process,
            sales_channel=sales_channel,
            language=language,
        )
        self.import_process = self.import_process.get_real_instance()
        self._workbook_parser = MiraklWorkbookParser()
        self._reverse_mapper = MiraklReverseProductMapper(sales_channel=self.sales_channel)
        self._offers_by_shop_sku: dict[str, dict[str, Any]] | None = None
        self._views_cache: list[MiraklSalesChannelView] | None = None

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

    def validate(self):
        export_files = list(self.import_process.export_files.all())
        if not export_files:
            raise MiraklImportMissingFilesError("Mirakl product import requires at least one export file.")

        sku_property_ids = list(
            MiraklProperty.objects.filter(
                sales_channel=self.sales_channel,
                representation_type=MiraklProperty.REPRESENTATION_PRODUCT_SKU,
            ).values_list("id", flat=True)
        )
        if not sku_property_ids:
            raise MiraklImportInvalidFileLayoutError(
                "Mirakl product import requires at least one Mirakl property mapped as product_sku."
            )

        property_by_code = {
            item.code: item
            for item in MiraklProperty.objects.filter(sales_channel=self.sales_channel)
        }

        for export_file in export_files:
            _filename, _labels, codes = self._workbook_parser.get_layout(export_file=export_file)
            missing_codes = [code for code in codes if code and code not in property_by_code]
            if missing_codes:
                raise MiraklImportInvalidFileLayoutError(
                    f"Mirakl import export file '{export_file.file.name}' contains unknown Mirakl property codes: {', '.join(missing_codes)}."
                )

            if not any(
                property_by_code[code].representation_type == MiraklProperty.REPRESENTATION_PRODUCT_SKU
                for code in codes
                if code in property_by_code
            ):
                raise MiraklImportInvalidFileLayoutError(
                    f"Mirakl import export file '{export_file.file.name}' does not contain a product_sku column."
                )

    def get_total_instances(self):
        total = 0
        for export_file in self.import_process.export_files.all():
            try:
                total += self._workbook_parser.count_rows(export_file=export_file)
            except (MiraklImportInvalidFileTypeError, MiraklImportInvalidFileLayoutError):
                continue
        self.import_process.total_records = total
        self.import_process.processed_records = 0
        self.import_process.save(update_fields=["total_records", "processed_records"])
        return total

    def get_products_data(self):
        return []

    def handle_ean_code(self, import_instance: ImportProductInstance):
        if not hasattr(import_instance, "ean_code") or getattr(import_instance, "remote_instance", None) is None:
            return

        queryset = MiraklEanCode.objects.filter(
            multi_tenant_company=self.import_process.multi_tenant_company,
            sales_channel=self.sales_channel,
            remote_product=import_instance.remote_instance,
        ).order_by("id")
        instances = list(queryset)
        instance = instances[0] if instances else None

        if instance is None:
            MiraklEanCode.objects.create(
                multi_tenant_company=self.import_process.multi_tenant_company,
                sales_channel=self.sales_channel,
                remote_product=import_instance.remote_instance,
                ean_code=import_instance.ean_code,
            )
            return

        duplicate_ids = [item.id for item in instances[1:]]
        if duplicate_ids:
            MiraklEanCode.objects.filter(id__in=duplicate_ids).delete()

        if instance.ean_code != import_instance.ean_code:
            instance.ean_code = import_instance.ean_code
            instance.save(update_fields=["ean_code"])

    def import_products_process(self):
        self._offers_by_shop_sku = self._load_offers_lookup()
        export_files = list(self.import_process.export_files.all())
        error_details_issues_cleared = False

        for export_file in export_files:
            imported_remote_products_by_row: dict[int, MiraklProduct] = {}
            imported_remote_products_by_identifier: dict[str, MiraklProduct] = {}
            for row in self._workbook_parser.iter_rows(export_file=export_file):
                try:
                    with transaction.atomic():
                        remote_product = self._process_row(row=row)
                        if remote_product is not None:
                            imported_remote_products_by_row[row.row_number] = remote_product
                            imported_remote_products_by_identifier[remote_product.local_instance.sku] = remote_product
                except Exception as exc:
                    if not self.import_process.skip_broken_records:
                        raise
                    self._add_broken_record(
                        code=self.ERROR_INVALID_ROW,
                        message="Mirakl row import failed.",
                        data=row.fields,
                        context={
                            "filename": row.filename,
                            "row_number": row.row_number,
                        },
                        exc=exc,
                    )
                finally:
                    self.update_percentage()

            error_rows = list(self._workbook_parser.iter_error_rows(export_file=export_file))
            if error_rows:
                if not error_details_issues_cleared:
                    MiraklProductIssue.objects.filter(
                        remote_product__sales_channel=self.sales_channel,
                        raw_data__source=self.ISSUE_SOURCE_ERROR_DETAILS,
                    ).delete()
                    error_details_issues_cleared = True
                self._sync_error_details_issues(
                    error_rows=error_rows,
                    remote_products_by_row=imported_remote_products_by_row,
                    remote_products_by_identifier=imported_remote_products_by_identifier,
                )

    def _process_row(self, *, row: MiraklImportRow) -> None:
        offers_lookup = self._offers_by_shop_sku or {}
        row_shop_sku = self._resolve_row_shop_sku(row=row)
        mapped_row = self._reverse_mapper.build(
            row_fields=row.fields,
            offer_data=offers_lookup.get(row_shop_sku, {}),
        )

        if mapped_row.is_configurable:
            return self._process_configurable_row(row=row, mapped_row=mapped_row)

        return self._process_simple_row(row=row, mapped_row=mapped_row)

    def _resolve_row_shop_sku(self, *, row: MiraklImportRow) -> str:
        for code, raw_value in row.fields.items():
            remote_property = self._reverse_mapper._property_by_code.get(code)
            if remote_property is None:
                continue
            if remote_property.representation_type != MiraklProperty.REPRESENTATION_PRODUCT_SKU:
                continue
            value = str(raw_value or "").strip()
            if value:
                return value
        return ""

    def _process_simple_row(self, *, row: MiraklImportRow, mapped_row: MiraklMappedRow) -> MiraklProduct:
        child_import = self._import_local_product(
            payload=mapped_row.child_payload,
            rule=mapped_row.rule,
        )
        remote_product = self._upsert_remote_product(
            local_product=child_import.instance,
            remote_sku=mapped_row.remote_sku,
            is_variation=False,
            parent_remote=None,
            mapped_row=mapped_row,
            row=row,
        )
        child_import.set_remote_instance(remote_product)

        self._detach_variation_links(product=child_import.instance)
        self.handle_ean_code(child_import)
        self.handle_translations(child_import)
        self.handle_prices(child_import)
        self.handle_images(child_import)
        self._sync_product_category(product=child_import.instance, category_code=mapped_row.category_code)
        self._sync_assigns(
            product=child_import.instance,
            remote_product=remote_product,
            view_codes=mapped_row.view_codes,
        )
        self._create_import_log(
            import_instance=child_import,
            raw_data={
                "row": row.fields,
                "offer": mapped_row.offer_data,
                "source": {"filename": row.filename, "row_number": row.row_number},
            },
            structured_data=mapped_row.child_payload,
        )
        return remote_product

    def _process_configurable_row(self, *, row: MiraklImportRow, mapped_row: MiraklMappedRow) -> MiraklProduct:
        parent_product = self._get_existing_product(sku=mapped_row.parent_sku)
        if parent_product is not None and parent_product.is_not_configurable():
            raise MiraklImportConfigurableConflictError(
                f"Mirakl configurable SKU '{mapped_row.parent_sku}' already exists as a non-configurable product."
            )

        parent_payload = dict(mapped_row.parent_payload or {})
        if parent_product is not None and self._product_has_channel_images(product=parent_product):
            parent_payload.pop("images", None)

        parent_import = self._import_local_product(
            payload=parent_payload,
            rule=mapped_row.rule,
            instance=parent_product,
        )
        parent_remote = self._upsert_remote_product(
            local_product=parent_import.instance,
            remote_sku=mapped_row.parent_sku,
            is_variation=False,
            parent_remote=None,
            mapped_row=mapped_row,
            row=row,
        )
        parent_import.set_remote_instance(parent_remote)
        self.handle_translations(parent_import)
        if parent_payload.get("images"):
            self.handle_images(parent_import)

        child_import = self._import_local_product(
            payload=mapped_row.child_payload,
            rule=mapped_row.rule,
        )
        child_remote = self._upsert_remote_product(
            local_product=child_import.instance,
            remote_sku=mapped_row.remote_sku,
            is_variation=True,
            parent_remote=parent_remote,
            mapped_row=mapped_row,
            row=row,
        )
        child_import.set_remote_instance(child_remote)

        self.handle_ean_code(child_import)
        self.handle_translations(child_import)
        self.handle_prices(child_import)
        self.handle_images(child_import)

        self._sync_configurable_relation(
            parent_product=parent_import.instance,
            child_product=child_import.instance,
        )
        self._sync_product_category(product=child_import.instance, category_code=mapped_row.category_code)
        self._sync_product_category(product=parent_import.instance, category_code=mapped_row.category_code)
        self._remove_assigns_for_product(product=child_import.instance, view_codes=mapped_row.view_codes)
        self._sync_assigns(
            product=parent_import.instance,
            remote_product=parent_remote,
            view_codes=mapped_row.view_codes,
        )
        self._sync_configurator(parent_remote=parent_remote, rule=mapped_row.rule)
        self._create_import_log(
            import_instance=child_import,
            raw_data={
                "row": row.fields,
                "offer": mapped_row.offer_data,
                "source": {"filename": row.filename, "row_number": row.row_number},
            },
            structured_data={
                "parent": parent_payload,
                "child": mapped_row.child_payload,
            },
        )
        return child_remote

    def _import_local_product(self, *, payload: dict[str, Any], rule, instance=None) -> ImportProductInstance:
        if not payload or not payload.get("sku"):
            raise MiraklImportInvalidRowError("Mirakl import payload is missing a SKU.")

        import_instance = ImportProductInstance(
            payload,
            import_process=self.import_process,
            rule=rule,
            sales_channel=self.sales_channel,
            instance=instance,
            update_current_rule=True,
        )
        import_instance.update_only = self.import_process.update_only
        import_instance.create_only = self.import_process.create_only
        import_instance.override_only = self.import_process.override_only
        import_instance.language = self.language
        import_instance.process()
        return import_instance

    def _upsert_remote_product(
        self,
        *,
        local_product: Product,
        remote_sku: str,
        is_variation: bool,
        parent_remote: MiraklProduct | None,
        mapped_row: MiraklMappedRow,
        row: MiraklImportRow,
    ) -> MiraklProduct:
        queryset = MiraklProduct.objects.filter(
            sales_channel=self.sales_channel,
            local_instance=local_product,
        )
        remote_product = None
        if is_variation and parent_remote is not None:
            remote_product = queryset.filter(remote_parent_product=parent_remote).first()
            if remote_product is None:
                remote_product = queryset.filter(remote_parent_product__isnull=True).first()
        else:
            remote_product = queryset.filter(remote_parent_product__isnull=True).first()
            if remote_product is None:
                remote_product = queryset.first()

        if remote_product is None:
            remote_product = MiraklProduct(
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=local_product,
            )

        updates: list[str] = []
        if remote_product.local_instance_id != local_product.id:
            remote_product.local_instance = local_product
            updates.append("local_instance")
        if remote_product.remote_sku != remote_sku:
            remote_product.remote_sku = remote_sku or None
            updates.append("remote_sku")
        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation
            updates.append("is_variation")
        desired_parent_id = getattr(parent_remote, "id", None)
        if remote_product.remote_parent_product_id != desired_parent_id:
            remote_product.remote_parent_product = parent_remote
            updates.append("remote_parent_product")
        if remote_product.syncing_current_percentage != 100:
            remote_product.syncing_current_percentage = 100
            updates.append("syncing_current_percentage")

        title = str(mapped_row.offer_data.get("product_name") or local_product.name or "").strip()
        brand = str(mapped_row.offer_data.get("brand") or "").strip()
        raw_data = {
            "import_source": "xlsx_reverse_import",
            "filename": row.filename,
            "row_number": row.row_number,
            "shop_sku": mapped_row.shop_sku,
            "category_code": mapped_row.category_code,
            "offer": mapped_row.offer_data,
        }
        if remote_product.title != title:
            remote_product.title = title
            updates.append("title")
        if remote_product.brand != brand:
            remote_product.brand = brand
            updates.append("brand")
        if remote_product.raw_data != raw_data:
            remote_product.raw_data = raw_data
            updates.append("raw_data")

        if remote_product.pk is None:
            remote_product.save()
            return remote_product

        if updates:
            remote_product.save(update_fields=updates)
        return remote_product

    def _sync_configurable_relation(self, *, parent_product: Product, child_product: Product) -> None:
        ConfigurableVariation.objects.get_or_create(
            parent=parent_product,
            variation=child_product,
            multi_tenant_company=self.multi_tenant_company,
        )

    def _detach_variation_links(self, *, product: Product) -> None:
        return

    def _sync_configurator(self, *, parent_remote: MiraklProduct, rule) -> None:
        if rule is None or parent_remote.local_instance is None:
            return
        variations = parent_remote.local_instance.get_configurable_variations(active_only=False)
        if hasattr(parent_remote, "configurator"):
            parent_remote.configurator.update_if_needed(
                rule=rule,
                variations=variations,
                send_sync_signal=False,
            )
            return
        RemoteProductConfigurator.objects.create_from_remote_product(
            remote_product=parent_remote,
            rule=rule,
            variations=variations,
        )

    def _sync_assigns(self, *, product: Product, remote_product: MiraklProduct, view_codes: list[str]) -> None:
        views = self._get_target_views(view_codes=view_codes)
        for view in views:
            assign, _ = SalesChannelViewAssign.objects.get_or_create(
                product=product,
                sales_channel_view=view,
                multi_tenant_company=self.multi_tenant_company,
                sales_channel=self.sales_channel,
                defaults={"remote_product": remote_product},
            )
            if assign.remote_product_id != remote_product.id:
                assign.remote_product = remote_product
                assign.save(update_fields=["remote_product"])

    def _remove_assigns_for_product(self, *, product: Product, view_codes: list[str]) -> None:
        views = self._get_target_views(view_codes=view_codes)
        view_ids = [view.id for view in views]
        SalesChannelViewAssign.objects.filter(
            product=product,
            sales_channel=self.sales_channel,
            sales_channel_view_id__in=view_ids,
        ).delete()

    def _sync_product_category(self, *, product: Product, category_code: str) -> None:
        category_code = str(category_code or "").strip()
        if not category_code:
            return
        try:
            category, created = MiraklProductCategory.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                product=product,
                sales_channel=self.sales_channel,
                defaults={"remote_id": category_code},
            )
        except ValidationError as exc:
            raise MiraklImportInvalidRowError(
                f"Invalid Mirakl category assignment '{category_code}' for product {product.sku}."
            ) from exc

        if created or category.remote_id == category_code:
            return

        category.remote_id = category_code
        try:
            category.save(update_fields=["remote_id"])
        except ValidationError as exc:
            raise MiraklImportInvalidRowError(
                f"Invalid Mirakl category assignment '{category_code}' for product {product.sku}."
            ) from exc

    def _load_offers_lookup(self) -> dict[str, dict[str, Any]]:
        offers = self.mirakl_paginated_get(
            path="/api/offers",
            results_key="offers",
        )
        lookup: dict[str, dict[str, Any]] = {}

        for offer in offers:
            if not isinstance(offer, dict):
                continue
            shop_sku = str(offer.get("shop_sku") or "").strip()
            if not shop_sku:
                continue

            if shop_sku in lookup:
                self._add_broken_record(
                    code=self.ERROR_DUPLICATE_OFFER_SHOP_SKU,
                    message="Duplicate Mirakl OF21 offer for the same shop_sku. Kept the first payload.",
                    data={"shop_sku": shop_sku, "offer_id": offer.get("offer_id")},
                )
                continue

            lookup[shop_sku] = {
                "price": self._first_non_empty(
                    offer.get("price"),
                    (offer.get("applicable_pricing") or {}).get("price"),
                ),
                "rrp": offer.get("msrp"),
                "condition": self._first_non_empty(offer.get("state_code")),
                "remote_sku": self._first_non_empty(offer.get("product_sku")),
                "brand": self._first_non_empty(offer.get("product_brand")),
                "product_name": self._first_non_empty(offer.get("product_title")),
                "product_description": self._first_non_empty(
                    offer.get("description"),
                    offer.get("product_description"),
                ),
                "product_short_description": self._first_non_empty(offer.get("internal_description")),
                "logistic_class": self._first_non_empty((offer.get("logistic_class") or {}).get("code")),
                "category_code": self._first_non_empty(offer.get("category_code")),
                "channels": offer.get("channels") or [],
                "currency": self._first_non_empty(offer.get("currency_iso_code")),
                "raw_offer": offer,
            }

        return lookup

    def _get_target_views(self, *, view_codes: list[str]) -> list[MiraklSalesChannelView]:
        if self._views_cache is None:
            self._views_cache = list(
                MiraklSalesChannelView.objects.filter(sales_channel=self.sales_channel).order_by("id")
            )
        if not view_codes:
            return self._views_cache
        filtered = [view for view in self._views_cache if str(view.remote_id or "").strip() in view_codes]
        return filtered or self._views_cache

    def _product_has_channel_images(self, *, product: Product) -> bool:
        return MediaProductThrough.objects.filter(
            product=product,
            sales_channel=self.sales_channel,
        ).exists()

    def _get_existing_product(self, *, sku: str) -> Product | None:
        return Product.objects.filter(
            sku=sku,
            multi_tenant_company=self.multi_tenant_company,
        ).first()

    def _create_import_log(
        self,
        *,
        import_instance: ImportProductInstance,
        raw_data: dict[str, Any],
        structured_data: dict[str, Any],
    ) -> None:
        if getattr(import_instance, "instance", None) is None:
            return

        log_instance = ImportProduct.objects.create(
            multi_tenant_company=self.multi_tenant_company,
            import_process=self.import_process,
            remote_product=getattr(import_instance, "remote_instance", None),
            raw_data=clean_json_data(raw_data),
            structured_data=clean_json_data(structured_data),
            successfully_imported=True,
            content_type=ContentType.objects.get_for_model(import_instance.instance),
            object_id=import_instance.instance.pk,
        )
        if getattr(import_instance, "remote_instance", None) is not None and log_instance.remote_product_id != import_instance.remote_instance.id:
            log_instance.remote_product = import_instance.remote_instance
            log_instance.save(update_fields=["remote_product"])

    def _sync_error_details_issues(
        self,
        *,
        error_rows: list[MiraklImportErrorRow],
        remote_products_by_row: dict[int, MiraklProduct],
        remote_products_by_identifier: dict[str, MiraklProduct],
    ) -> None:
        for error_row in error_rows:
            remote_product = self._resolve_error_row_remote_product(
                error_row=error_row,
                remote_products_by_row=remote_products_by_row,
                remote_products_by_identifier=remote_products_by_identifier,
            )
            if remote_product is None:
                continue

            issue_code, issue_message = self._parse_error_code_and_message(
                error_code=error_row.fields.get("error_code"),
                error_message=error_row.fields.get("error_message"),
            )
            issue = MiraklProductIssue.objects.create(
                multi_tenant_company=remote_product.multi_tenant_company,
                remote_product=remote_product,
                main_code=issue_code,
                code=issue_code,
                message=issue_message,
                severity="ERROR",
                reason_label=error_row.fields.get("attribute_label") or None,
                attribute_code=error_row.fields.get("attribute_codes") or None,
                is_rejected=False,
                raw_data={
                    "source": self.ISSUE_SOURCE_ERROR_DETAILS,
                    "import_id": self.import_process.id,
                    "line_number": error_row.fields.get("line_number"),
                    "provider_unique_identifier": error_row.fields.get("provider_unique_identifier"),
                    "row": error_row.fields,
                },
            )
            views = self._get_target_views(
                view_codes=self._parse_channels(value=error_row.fields.get("channels", "")),
            )
            if views:
                issue.views.set(views)

            remote_product.refresh_status(commit=True)

    def _resolve_error_row_remote_product(
        self,
        *,
        error_row: MiraklImportErrorRow,
        remote_products_by_row: dict[int, MiraklProduct],
        remote_products_by_identifier: dict[str, MiraklProduct],
    ) -> MiraklProduct | None:
        raw_line_number = str(error_row.fields.get("line_number") or "").strip()
        if raw_line_number.isdigit():
            remote_product = remote_products_by_row.get(int(raw_line_number))
            if remote_product is not None:
                return remote_product

        provider_identifier = str(error_row.fields.get("provider_unique_identifier") or "").strip()
        if provider_identifier:
            remote_product = remote_products_by_identifier.get(provider_identifier)
            if remote_product is not None:
                return remote_product

        return None

    def _parse_error_code_and_message(self, *, error_code: str | None, error_message: str | None) -> tuple[str | None, str | None]:
        normalized_code = str(error_code or "").strip()
        normalized_message = str(error_message or "").strip() or None
        if " : " in normalized_code:
            code, detail = normalized_code.split(" : ", 1)
            normalized_code = code.strip() or None
            if not normalized_message:
                normalized_message = detail.strip() or None
        else:
            normalized_code = normalized_code or None
        return normalized_code, normalized_message

    def _parse_channels(self, *, value: str) -> list[str]:
        raw = str(value or "").replace(";", ",")
        return [chunk.strip() for chunk in raw.split(",") if chunk.strip()]

    def _first_non_empty(self, *values):
        for value in values:
            if value in (None, "", [], {}):
                continue
            return value
        return ""
