from __future__ import annotations

import inspect
import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional

from currencies.models import Currency
from products.models import ProductTranslation
from properties.models import ProductPropertiesRuleItem, ProductProperty, Property
from sales_channels.factories.products.products import (
    RemoteProductCreateFactory,
    RemoteProductSyncFactory,
    RemoteProductDeleteFactory,
    RemoteProductUpdateFactory,
)
from sales_channels.integrations.shein.factories.mixins import SheinSignatureMixin
from sales_channels.integrations.shein.factories.products.assigns import SheinSalesChannelAssignFactoryMixin
from sales_channels.integrations.shein.factories.products.documents import (
    SheinDocumentThroughProductCreateFactory,
    SheinDocumentThroughProductDeleteFactory,
    SheinDocumentThroughProductUpdateFactory,
)
from sales_channels.integrations.shein.factories.products.external_documents import (
    SheinProductExternalDocumentsFactory,
)
from sales_channels.integrations.shein.factories.products.images import SheinMediaProductThroughUpdateFactory
from sales_channels.integrations.shein.factories.prices import SheinPriceUpdateFactory
from sales_channels.integrations.shein.factories.properties import SheinProductPropertyUpdateFactory
from sales_channels.integrations.shein.helpers.certificate_types import (
    is_certificate_type_uploadable,
)
from sales_channels.integrations.shein.exceptions import (
    SheinConfiguratorAttributesLimitError,
    SheinPreValidationError,
    SheinResponseException,
)
from sales_channels.exceptions import PreFlightCheckError, SkipSyncBecauseOfStatusException
from sales_channels.integrations.shein.models import (
    SheinCategory,
    SheinDocumentThroughProduct,
    SheinDocumentType,
    SheinInternalProperty,
    SheinPrice,
    SheinProduct,
    SheinProductCategory,
    SheinProductContent,
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
from sales_channels.integrations.shein.helpers.local_instances import describe_local_instance

logger = logging.getLogger(__name__)


class SheinProductBaseFactory(
    SheinSignatureMixin,
    SheinSalesChannelAssignFactoryMixin,
    RemoteProductSyncFactory,
):
    """Assemble Shein product payloads using existing value-only factories."""

    remote_model_class = SheinProduct
    action_log = RemoteLog.ACTION_UPDATE
    integration_has_documents = True
    remote_document_assign_model_class = SheinDocumentThroughProduct
    remote_document_assign_create_factory = SheinDocumentThroughProductCreateFactory
    remote_document_assign_update_factory = SheinDocumentThroughProductUpdateFactory
    remote_document_assign_delete_factory = SheinDocumentThroughProductDeleteFactory
    publish_permission_path = "/open-api/goods/product/check-publish-permission"
    publish_or_edit_path = "/open-api/goods/product/publishOrEdit"
    default_dimension_value = "10"
    default_weight_value = 10
    supplier_barcode_type = "EAN"
    _EAN_DIGITS_RE = re.compile(r"\D+")

    def get_identifiers(self, *, fixing_caller: str = "run"):
        frame = inspect.currentframe()
        caller = frame.f_back.f_code.co_name
        class_name = SheinProductBaseFactory.__name__

        fixing_class = getattr(self, "fixing_identifier_class", None)
        fixing_identifier = None
        if fixing_caller and fixing_class:
            fixing_identifier = f"{fixing_class.__name__}:{fixing_caller}"

        return f"{class_name}:{caller}", fixing_identifier

    def process_content_translation(
        self,
        *,
        short_description,
        description,
        url_key,
        remote_language,
    ) -> None:
        # Shein payloads are handled via _build_translations; no per-translation persistence needed.
        return

    def __init__(
        self,
        *,
        sales_channel,
        local_instance,
        remote_instance=None,
        parent_local_instance=None,
        remote_parent_product=None,
        api=None,
        is_switched: bool = False,
        get_value_only: bool = False,
        skip_checks: bool = False,
        skip_price_update: bool = False,
        skip_property_values_category_validation: bool = True, # shein is weird, sometimes it let you even if the value is not in the approved list
    ) -> None:
        self.get_value_only = get_value_only
        self.skip_checks = skip_checks
        self.skip_price_update = skip_price_update
        self.skip_property_values_category_validation = skip_property_values_category_validation
        self.prices_data: dict[str, dict[str, Any]] = {}
        self.price_info_list: list[dict[str, Any]] = []
        self.image_info: dict[str, Any] = {}
        self.sale_attribute: Optional[dict[str, Any]] = None
        self.sale_attribute_list: list[dict[str, Any]] = []
        self.sale_attribute_sort_list: list[dict[str, Any]] = []
        self.size_attribute_list: list[dict[str, Any]] = []
        self.product_attribute_list: list[dict[str, Any]] = []
        self.multi_language_name_list: list[dict[str, str]] = []
        self.multi_language_desc_list: list[dict[str, str]] = []
        self.skc_list: list[dict[str, Any]] = []
        self.has_quantity_info = False
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

    def assign_documents(self):  # type: ignore[override]
        """Shein documents are synced after publish in final_process."""
        return

    def assign_ean_code(self):  # type: ignore[override]
        """Shein barcode is embedded into the SKU payload; skip remote EAN mirror processing."""
        return

    def final_process(self):
        if self.get_value_only:
            return
        if self.is_variation:
            return
        self.sync_documents_after_publish()

    def run_on_skip_sync_status(self):
        # Even when Shein blocks product edits during review, keep certificate sync attempt available.
        self.final_process()

    def sync_documents_after_publish(self):
        target_remote_products = self._get_document_target_remote_products()
        if not target_remote_products:
            self._sync_pending_external_documents(log_missing=True)
            return

        certificate_rule_records = self._get_certificate_rule_records_by_spu()
        allowed_remote_document_type_ids = self._get_allowed_document_type_remote_ids_by_spu(
            certificate_rule_records=certificate_rule_records,
        )
        self._validate_required_document_types_for_spu(
            certificate_rule_records=certificate_rule_records,
        )

        if allowed_remote_document_type_ids:
            document_throughs = self._get_document_throughs_for_sync(
                allowed_remote_document_type_ids=allowed_remote_document_type_ids,
            )
            if document_throughs:
                used_skc: set[str] = set()
                for target_remote_product in target_remote_products:
                    skc_name = str(getattr(target_remote_product, "skc_name", None) or "").strip()
                    if skc_name:
                        if skc_name in used_skc:
                            continue
                        used_skc.add(skc_name)

                    synced_association_ids = []
                    for media_through in document_throughs:
                        remote_association = self._sync_document_assignment_for_remote_product(
                            media_through=media_through,
                            remote_product=target_remote_product,
                            allowed_remote_document_type_ids=allowed_remote_document_type_ids,
                        )
                        if remote_association is not None:
                            synced_association_ids.append(remote_association.id)

                    stale_associations = self.remote_document_assign_model_class.objects.filter(
                        remote_product=target_remote_product,
                        sales_channel=self.sales_channel,
                        local_instance__product=self.local_instance,
                    ).exclude(id__in=synced_association_ids)
                    for remote_document_assoc in stale_associations.iterator():
                        self._delete_document_assignment_for_remote_product(
                            remote_document_assoc=remote_document_assoc,
                            remote_product=target_remote_product,
                        )

        self._sync_pending_external_documents(log_missing=True)

    def _get_document_target_remote_products(self) -> list[SheinProduct]:
        if self.remote_instance is None:
            return []

        if not self.local_instance.is_configurable():
            return [self.remote_instance]

        variations = list(
            self.remote_model_class.objects.filter(
                sales_channel=self.sales_channel,
                remote_parent_product=self.remote_instance,
                is_variation=True,
            )
            .exclude(skc_name__isnull=True)
            .exclude(skc_name="")
            .order_by("id")
        )
        if variations:
            unique_variations_by_skc: list[SheinProduct] = []
            seen_skc_names: set[str] = set()
            for variation in variations:
                skc_name = str(getattr(variation, "skc_name", None) or "").strip()
                if not skc_name or skc_name in seen_skc_names:
                    continue
                seen_skc_names.add(skc_name)
                unique_variations_by_skc.append(variation)
            if unique_variations_by_skc:
                return unique_variations_by_skc

        return [self.remote_instance]

    def _get_document_target_spu_name(self) -> str:
        remote_instance = getattr(self, "remote_instance", None)
        if remote_instance is None:
            return ""
        return str(
            getattr(remote_instance, "spu_name", None)
            or getattr(remote_instance, "remote_id", None)
            or ""
        ).strip()

    def _get_certificate_rule_records_by_spu(self) -> list[dict[str, Any]]:
        spu_name = self._get_document_target_spu_name()
        if not spu_name:
            return []

        try:
            records = self.get_certificate_rule_by_product_spu(spu_name=spu_name)
        except Exception as exc:
            raise PreFlightCheckError(
                f"Failed to fetch Shein certificate rules for SPU '{spu_name}'. Error: {exc}"
            ) from exc

        if not isinstance(records, list):
            return []
        return [record for record in records if isinstance(record, dict)]

    @staticmethod
    def _is_dimension_one_certificate_rule(*, record: dict[str, Any]) -> bool:
        dimension = str(record.get("certificateDimension") or "").strip()
        return not dimension or dimension == "1"

    @staticmethod
    def _is_required_certificate_rule(*, record: dict[str, Any]) -> bool:
        value = record.get("isRequired")
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        return False

    def _get_allowed_document_type_remote_ids_by_spu(
        self,
        *,
        certificate_rule_records: Optional[list[dict[str, Any]]] = None,
    ) -> set[str]:
        records = (
            certificate_rule_records
            if certificate_rule_records is not None
            else self._get_certificate_rule_records_by_spu()
        )
        remote_type_ids: set[str] = set()
        for record in records:
            if not self._is_dimension_one_certificate_rule(record=record):
                continue
            certificate_type_id = str(record.get("certificateTypeId") or "").strip()
            if certificate_type_id and is_certificate_type_uploadable(
                sales_channel=self.sales_channel,
                certificate_type_id=certificate_type_id,
            ):
                remote_type_ids.add(certificate_type_id)
        return remote_type_ids

    @staticmethod
    def _resolve_required_document_type_name(
        *,
        remote_id: str,
        rule_name_by_remote_id: dict[str, str],
        shein_type_by_remote_id: dict[str, "SheinDocumentType"],
    ) -> str:
        shein_type = shein_type_by_remote_id.get(remote_id)
        if shein_type is not None:
            translated_name = str(getattr(shein_type, "translated_name", "") or "").strip()
            if translated_name:
                return translated_name
            fallback_name = str(getattr(shein_type, "name", "") or "").strip()
            if fallback_name:
                return fallback_name

        rule_name = str(rule_name_by_remote_id.get(remote_id, "") or "").strip()
        if rule_name:
            return rule_name
        return remote_id

    def _validate_required_document_types_for_spu(
        self,
        *,
        certificate_rule_records: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        records = (
            certificate_rule_records
            if certificate_rule_records is not None
            else self._get_certificate_rule_records_by_spu()
        )
        if not records:
            return

        required_remote_ids: list[str] = []
        rule_name_by_remote_id: dict[str, str] = {}
        for record in records:
            if not self._is_dimension_one_certificate_rule(record=record):
                continue
            if not self._is_required_certificate_rule(record=record):
                continue

            remote_id = str(record.get("certificateTypeId") or "").strip()
            if not remote_id:
                continue
            if not is_certificate_type_uploadable(
                sales_channel=self.sales_channel,
                certificate_type_id=remote_id,
            ):
                continue
            if remote_id not in required_remote_ids:
                required_remote_ids.append(remote_id)
            if remote_id not in rule_name_by_remote_id:
                rule_name_by_remote_id[remote_id] = str(record.get("certificateTypeValue") or "").strip()

        if not required_remote_ids:
            return

        shein_document_types = list(
            SheinDocumentType.objects.filter(
                sales_channel=self.sales_channel,
                remote_id__in=required_remote_ids,
            )
            .exclude(remote_id__in=(None, ""))
            .only("remote_id", "translated_name", "name", "local_instance_id")
        )
        shein_type_by_remote_id = {
            str(remote_document_type.remote_id): remote_document_type
            for remote_document_type in shein_document_types
        }

        mapped_remote_ids = {
            str(remote_document_type.remote_id)
            for remote_document_type in shein_document_types
            if getattr(remote_document_type, "local_instance_id", None)
        }

        document_throughs = list(
            self.get_documents().select_related("media", "media__document_type")
        )
        local_document_type_ids = {
            media_through.media.document_type_id
            for media_through in document_throughs
            if getattr(getattr(media_through, "media", None), "document_type_id", None)
        }

        provided_remote_ids: set[str] = set()
        if local_document_type_ids:
            provided_remote_ids = {
                str(remote_id)
                for remote_id in (
                    SheinDocumentType.objects.filter(
                        sales_channel=self.sales_channel,
                        remote_id__in=required_remote_ids,
                        local_instance_id__in=local_document_type_ids,
                    )
                    .exclude(remote_id__in=(None, ""))
                    .values_list("remote_id", flat=True)
                )
            }

        unsatisfied_remote_ids = [
            remote_id
            for remote_id in required_remote_ids
            if remote_id not in provided_remote_ids
        ]
        if not unsatisfied_remote_ids:
            return

        missing_mapping_remote_ids = [
            remote_id for remote_id in unsatisfied_remote_ids if remote_id not in mapped_remote_ids
        ]
        missing_document_remote_ids = [
            remote_id for remote_id in unsatisfied_remote_ids if remote_id in mapped_remote_ids
        ]

        missing_mapping_labels = [
            self._resolve_required_document_type_name(
                remote_id=remote_id,
                rule_name_by_remote_id=rule_name_by_remote_id,
                shein_type_by_remote_id=shein_type_by_remote_id,
            )
            for remote_id in missing_mapping_remote_ids
        ]
        missing_document_labels = [
            self._resolve_required_document_type_name(
                remote_id=remote_id,
                rule_name_by_remote_id=rule_name_by_remote_id,
                shein_type_by_remote_id=shein_type_by_remote_id,
            )
            for remote_id in missing_document_remote_ids
        ]

        problems: list[str] = []
        if missing_mapping_labels:
            problems.extend(f"{label} (not mapped)" for label in missing_mapping_labels)
        if missing_document_labels:
            problems.extend(f"{label} (missing document)" for label in missing_document_labels)

        raise PreFlightCheckError(
            "Required Shein document types are not mapped or missing locally: "
            + ", ".join(problems)
            + ". Map these Shein document types and attach the required documents before publishing."
        )

    def _sync_pending_external_documents(self, *, log_missing: bool) -> bool:
        root_remote_product = getattr(self, "remote_instance", None)
        if root_remote_product is None:
            return False

        factory = SheinProductExternalDocumentsFactory(
            sales_channel=self.sales_channel,
            remote_product=root_remote_product,
        )
        return factory.apply(
            log_missing=log_missing,
            action=self.action_log,
        )

    def _get_document_type_map_by_local_instance_id(
        self,
        *,
        local_document_type_ids: set[int],
        allowed_remote_document_type_ids: set[str],
    ) -> dict[int, SheinDocumentType]:
        if not local_document_type_ids:
            return {}

        queryset = (
            SheinDocumentType.objects.filter(
                sales_channel=self.sales_channel,
                local_instance_id__in=local_document_type_ids,
            )
            .exclude(local_instance_id__isnull=True)
            .exclude(remote_id__in=(None, ""))
            .select_related("local_instance")
            .order_by("id")
        )
        if allowed_remote_document_type_ids:
            queryset = queryset.filter(remote_id__in=allowed_remote_document_type_ids)

        mapped: dict[int, SheinDocumentType] = {}
        for remote_document_type in queryset:
            local_instance_id = remote_document_type.local_instance_id
            if local_instance_id and local_instance_id not in mapped:
                mapped[local_instance_id] = remote_document_type
        return mapped

    def _get_document_throughs_for_sync(
        self,
        *,
        allowed_remote_document_type_ids: set[str],
    ):
        document_throughs_qs = self.get_documents().select_related("media", "media__document_type")
        document_throughs = list(document_throughs_qs)
        local_document_type_ids = {
            media_through.media.document_type_id
            for media_through in document_throughs
            if getattr(getattr(media_through, "media", None), "document_type_id", None)
        }
        mapped_types = self._get_document_type_map_by_local_instance_id(
            local_document_type_ids=local_document_type_ids,
            allowed_remote_document_type_ids=allowed_remote_document_type_ids,
        )

        eligible_document_throughs = []
        for media_through in document_throughs:
            media = getattr(media_through, "media", None)
            local_document_type_id = getattr(media, "document_type_id", None)
            if not local_document_type_id:
                continue
            if local_document_type_id not in mapped_types:
                continue
            eligible_document_throughs.append(media_through)

        return eligible_document_throughs

    def _sync_document_assignment_for_remote_product(
        self,
        *,
        media_through,
        remote_product,
        allowed_remote_document_type_ids: set[str],
    ):
        existing_association = self.remote_document_assign_model_class.objects.filter(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            remote_product=remote_product,
        ).select_related("remote_document", "remote_document__remote_document_type").first()

        factory = self.remote_document_assign_update_factory(
            local_instance=media_through,
            sales_channel=self.sales_channel,
            remote_instance=existing_association,
            remote_product=remote_product,
            api=self.api,
            skip_checks=True,
            get_value_only=getattr(self, "get_value_only", False),
            allowed_remote_document_type_ids=allowed_remote_document_type_ids,
        )
        factory.run()
        remote_instance = factory.remote_instance
        if remote_instance is None:
            return None
        return (
            remote_instance.__class__.objects.select_related(
                "remote_document",
                "remote_document__remote_document_type",
            )
            .filter(pk=remote_instance.pk)
            .first()
        )

    def _delete_document_assignment_for_remote_product(
        self,
        *,
        remote_document_assoc,
        remote_product,
    ):
        factory = self.remote_document_assign_delete_factory(
            local_instance=remote_document_assoc.local_instance,
            sales_channel=self.sales_channel,
            remote_instance=remote_document_assoc,
            remote_product=remote_product,
            api=self.api,
            skip_checks=True,
            get_value_only=getattr(self, "get_value_only", False),
        )
        factory.run()


    def preflight_check(self):
        if self.skip_checks:
            return True
        try:
            response = self.shein_get(path=self.publish_permission_path)
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

    def check_status(self, *, remote_product=None):
        remote_product = remote_product or getattr(self, "remote_product", None)
        if remote_product is None:
            return

        if getattr(remote_product, "status", None) != self.remote_model_class.STATUS_PENDING_APPROVAL:
            return

        if not getattr(remote_product, "spu_name", None):
            return

        message = (
            "This product is pending approval on Shein, so updates are paused until the review completes."
        )
        raise SkipSyncBecauseOfStatusException(message)

    def set_rule(self):
        self.rule = None
        self.selected_category_id = ""
        self.selected_product_type_id = ""
        self.use_spu_pic = False

        mapping = (
            SheinProductCategory.objects.filter(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                product=self.local_instance,
            )
            .exclude(remote_id__in=(None, ""))
            .only("remote_id", "product_type_remote_id")
            .first()
        )

        if mapping is not None:
            self.selected_category_id = str(getattr(mapping, "remote_id", "") or "").strip()
            self.selected_product_type_id = str(getattr(mapping, "product_type_remote_id", "") or "").strip()

            if self.selected_category_id and not self.selected_product_type_id:
                category_qs = SheinCategory.objects.filter(remote_id=self.selected_category_id)
                category_qs = category_qs.filter(sales_channel=self.sales_channel)
                category_qs = category_qs.filter(
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                )
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
            raise PreFlightCheckError(
                "Missing Shein category or product type. Set the SheinProductCategory (category + product_type_id) "
                "or map the product rule to a SheinProductType."
            )

        self.use_spu_pic = self._resolve_use_spu_pic()


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

        categories = SheinCategory.objects.filter(
            remote_id=self.selected_category_id,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )

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

    def _supports_sale_attribute_sort(self) -> bool:
        if not self.selected_category_id:
            return False

        categories = SheinCategory.objects.filter(remote_id=self.selected_category_id)
        categories = categories.filter(sales_channel=self.sales_channel)
        categories = categories.filter(
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )

        category = categories.only("support_sale_attribute_sort").first()
        return bool(category and category.support_sale_attribute_sort)

    # ------------------------------------------------------------------
    # Payload builders
    # ------------------------------------------------------------------
    def _get_default_language(self) -> str:
        category_id = getattr(self, "selected_category_id", None)
        if category_id:
            category = (
                SheinCategory.objects.filter(
                    remote_id=category_id,
                    sales_channel=self.sales_channel,
                    multi_tenant_company=self.sales_channel.multi_tenant_company,
                )
                .only("default_language")
                .first()
            )
            if category and category.default_language:
                return category.default_language

        company = getattr(self.sales_channel, "multi_tenant_company", None)
        return getattr(company, "language", None) or TranslationFieldsMixin.LANGUAGES[0][0]

    def _build_translations(self):
        translations = list(self.local_instance.translations.all())
        if not translations:
            return

        default_language = self._get_default_language()
        from sales_channels.integrations.shein.models import SheinRemoteLanguage

        remote_language_qs = (
            SheinRemoteLanguage.objects.filter(
                sales_channel=self.sales_channel,
                local_instance__isnull=False,
            )
            .exclude(local_instance="")
            .order_by("id")
        )
        allowed_languages: list[str] = []
        for entry in remote_language_qs:
            language = entry.local_instance
            if language and language not in allowed_languages:
                allowed_languages.append(language)
        if not allowed_languages:
            allowed_languages = [default_language]

        name_by_language: dict[str, str] = {}
        desc_by_language: dict[str, str] = {}
        sales_channel_id = self.sales_channel.id
        channel_translations: dict[str, ProductTranslation] = {}
        default_translations: dict[str, ProductTranslation] = {}

        for translation in translations:
            language = translation.language or default_language
            if not language:
                continue
            translation_sales_channel_id = getattr(translation, "sales_channel_id", None)
            if translation_sales_channel_id == sales_channel_id:
                channel_translations[language] = translation
            elif translation_sales_channel_id is None:
                default_translations[language] = translation

        for language in allowed_languages:
            selected = channel_translations.get(language) or default_translations.get(language)
            if selected is None:
                continue

            fallback = default_translations.get(language)
            name = selected.name
            if not name and fallback is not None and fallback is not selected:
                name = fallback.name
            if name:
                name_by_language[language] = name

            description = selected.description or selected.short_description
            if fallback is not None and fallback is not selected:
                fallback_desc = fallback.description or fallback.short_description
                if not description or (
                    self._is_blank_html(description)
                    and fallback_desc
                    and not self._is_blank_html(fallback_desc)
                ):
                    description = fallback_desc
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

    def _use_create_payload(self) -> bool:
        if getattr(self, "is_create", False):
            return True
        remote_instance = getattr(self, "remote_instance", None)
        if remote_instance is None:
            return True
        return not bool(getattr(remote_instance, "spu_name", None))

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

        rule_properties_qs = self.local_instance.get_required_and_optional_properties(
            product_rule=self.rule,
            sales_channel=self.sales_channel,
        )
        if self.local_instance.is_configurable():
            rule_properties_qs = rule_properties_qs.exclude(
                type__in=(
                    ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
                    ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR,
                )
            )
        rule_properties_ids = rule_properties_qs.values_list("property_id", flat=True)

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
        relevant_only: bool = False,
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
            if relevant_only and not self._resolve_type_item_for_property(product_property=product_property):
                continue
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

    def _resolve_type_items_for_property(
        self,
        *,
        product_property: ProductProperty,
    ) -> list[SheinProductTypeItem]:
        return list(
            SheinProductTypeItem.objects.filter(
                product_type__sales_channel=self.sales_channel,
                product_type__remote_id=self.selected_product_type_id,
                property__local_instance=product_property.property,
            ).select_related("property")
        )

    def _resolve_type_item_for_property(
        self,
        *,
        product_property: ProductProperty,
    ) -> Optional[SheinProductTypeItem]:
        type_items = self._resolve_type_items_for_property(product_property=product_property)
        return type_items[0] if type_items else None

    def _get_approved_value_labels(
        self,
        *,
        type_item: SheinProductTypeItem,
        approved_value_ids: set[str],
    ) -> list[str]:
        if not approved_value_ids:
            return []
        from sales_channels.integrations.shein.models import SheinPropertySelectValue

        values = (
            SheinPropertySelectValue.objects.filter(
                remote_property=type_item.property,
                remote_id__in=approved_value_ids,
            )
            .values_list("remote_id", "value", "value_en")
        )
        label_by_id = {}
        for remote_id, value, value_en in values:
            label = value or value_en or str(remote_id)
            label_by_id[str(remote_id)] = label

        labels = {label_by_id.get(str(value), str(value)) for value in approved_value_ids}
        return sorted(labels)

    def _get_allowed_values_display(
        self,
        *,
        type_item: SheinProductTypeItem,
        approved_value_ids: set[str],
    ) -> str:
        cache = getattr(self, "_approved_values_display_cache", {})
        key = (type_item.id, tuple(sorted(approved_value_ids)))
        if key not in cache:
            approved_value_labels = self._get_approved_value_labels(
                type_item=type_item,
                approved_value_ids=approved_value_ids,
            )
            cache[key] = ", ".join(approved_value_labels or sorted(approved_value_ids))
            self._approved_values_display_cache = cache
        return cache[key]

    def _validate_approved_values_for_category(
        self,
        *,
        type_item: SheinProductTypeItem,
        product_property: ProductProperty,
        attribute_value_id: Any,
    ) -> None:
        approved_value_ids = {
            str(value)
            for value in (type_item.approved_value_ids or [])
            if value not in (None, "")
        }
        if (
            not approved_value_ids
            or attribute_value_id in (None, "", [])
            or self.skip_property_values_category_validation
        ):
            return

        details = describe_local_instance(local_instance=product_property)
        allowed_values = self._get_allowed_values_display(
            type_item=type_item,
            approved_value_ids=approved_value_ids,
        )
        if isinstance(attribute_value_id, (list, tuple, set)):
            invalid_values = [
                str(value)
                for value in attribute_value_id
                if str(value) not in approved_value_ids
            ]
            if invalid_values:
                raise PreFlightCheckError(
                    "Shein value(s) {} for {} are not approved for category {} (allowed: {}).".format(
                        ", ".join(invalid_values),
                        details,
                        type_item.product_type.category_id,
                        allowed_values,
                    )
                )
            return

        if str(attribute_value_id) not in approved_value_ids:
            raise PreFlightCheckError(
                "Shein value {} for {} is not approved for category {} (allowed: {}).".format(
                    attribute_value_id,
                    details,
                    type_item.product_type.category_id,
                    allowed_values,
                )
            )

    def _build_property_payloads(self):
        for product_property in self._collect_product_properties():
            type_items = self._resolve_type_items_for_property(product_property=product_property)
            if not type_items:
                continue

            for type_item in type_items:
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

                self._validate_approved_values_for_category(
                    type_item=type_item,
                    product_property=product_property,
                    attribute_value_id=payload.get("attribute_value_id"),
                )

                attribute_type = payload.get("attribute_type")
                payload.pop("attribute_type", None)

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
            include_all_prices=self._use_create_payload(),
            assigns=assigns,
        )
        price_factory.run()
        self.prices_data = getattr(price_factory, "price_data", {}) or {}
        self.price_info_list = price_factory.value.get("price_info_list", []) if price_factory.value else []

    def _build_media(self):
        self.image_info = self._build_image_info_for_product(product=self.local_instance)

    def _build_image_info_for_product(self, *, product, remote_product=None) -> dict[str, Any]:
        media_factory = SheinMediaProductThroughUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=None,
            remote_product=remote_product or self.remote_instance,
            get_value_only=True,
            skip_checks=True,
            product_instance=product,
        )
        media_factory.run()
        return media_factory.value.get("image_info", {}) if media_factory.value else {}

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

    def _build_sku_price_info_list(
        self,
        *,
        assigns: list[SalesChannelViewAssign],
        product=None,
    ) -> list[dict[str, Any]]:
        currency_map = self._get_assign_currency_map(assigns=assigns)
        if assigns and not currency_map:
            raise PreFlightCheckError(
                "Shein currency mapping is missing for assigned sub-sites. Pull Shein site list metadata first."
            )

        product = product or self.local_instance

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

            local_currency = Currency.objects.filter(
                iso_code=currency_code,
                multi_tenant_company=self.sales_channel.multi_tenant_company,
            ).first()
            if local_currency is None:
                missing.append(sub_site_code)
                continue
            full_price, discount_price = product.get_price_for_sales_channel(
                self.sales_channel,
                currency=local_currency,
            )
            base_price = float(full_price) if full_price is not None else None
            special_price = float(discount_price) if discount_price is not None else None

            entry = {
                "currency": currency_code,
                "base_price": base_price,
                "special_price": special_price,
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

    def _resolve_supplier_code(self, *, product=None, required: bool = False) -> str | None:
        product = product or self.local_instance
        value = self._get_internal_property_value(code="supplier_code", default=None, product=product)
        if value in (None, "", []):
            fallback = getattr(product, "sku", None)
            return str(fallback).strip() if fallback else None
        return str(value).strip()

    def _build_quantity_info(self, *, product=None) -> dict[str, Any] | None:
        product = product or self.local_instance
        unit_value = self._get_internal_property_option_value(code="quantity_info__unit", product=product)
        quantity_value = self._get_internal_property_value(
            code="quantity_info__quantity",
            default=None,
            product=product,
        )
        if unit_value in (None, "", []) or quantity_value in (None, "", []):
            return None
        try:
            quantity_decimal = Decimal(str(quantity_value))
        except (InvalidOperation, TypeError, ValueError):
            return None
        if quantity_decimal != quantity_decimal.to_integral_value():
            raise PreFlightCheckError(
                f"Shein quantity_info__quantity must be a whole number. Received: {quantity_value}."
            )
        quantity = int(quantity_decimal)
        if quantity <= 0:
            return None
        try:
            unit = int(unit_value)
        except (TypeError, ValueError):
            return None
        if unit not in (1, 2):
            return None
        quantity_type = 1 if quantity == 1 else 2
        return {
            "quantity_type": quantity_type,
            "quantity_unit": unit,
            "quantity": quantity,
        }

    def _build_fill_configuration_info(
        self,
        *,
        package_type: str | None,
        filled_quantity_to_sku: bool,
    ) -> dict[str, Any] | None:
        if not package_type and not filled_quantity_to_sku:
            return None
        payload: dict[str, Any] = {}
        tags: list[str] = []
        if package_type:
            tags.append("PACKAGE_TYPE_TO_SKU")
        if tags:
            payload["fill_configuration_tags"] = tags
        if filled_quantity_to_sku:
            payload["filled_quantity_to_sku"] = True
        return payload

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
            details = describe_local_instance(local_instance=product_property)
            raise PreFlightCheckError(
                f"Shein product type item mapping is missing for a configurator property{details}."
            )

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
            details = describe_local_instance(local_instance=product_property)
            raise PreFlightCheckError(
                f"Unable to render Shein sale attribute payload for a configurator property{details}."
            )

        try:
            raw_payload = json.loads(remote_value)
        except (TypeError, ValueError):
            details = describe_local_instance(local_instance=product_property)
            raise PreFlightCheckError(
                f"Invalid Shein sale attribute payload for configurator property{details}."
            )

        self._validate_approved_values_for_category(
            type_item=type_item,
            product_property=product_property,
            attribute_value_id=raw_payload.get("attribute_value_id"),
        )
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

        def is_varying(item: ProductPropertiesRuleItem, vary_by=1) -> bool:
            return len(varying_map.get(item.property_id, set())) > vary_by

        # Primary must be a "main" sales attribute that has at least one value present.
        # If any "main" attribute has multiple values across variations, pick that one as primary.
        # If no main attribute varies, pick the first main attribute that has at least one value.
        primary_candidates = [
            item
            for item in items
            if self._is_main_sales_attribute(
                property_id=item.property_id,
                variation_properties=variation_properties,
            )
            and is_varying(item, vary_by=0)
        ]
        if not primary_candidates:
            raise PreFlightCheckError(
                "Shein requires at least one main sales attribute with values."
            )
        primary = next((item for item in primary_candidates if is_varying(item)), None)
        if primary is None:
            primary = primary_candidates[0]

        # SKU-level attributes are the remaining varying attributes, excluding the primary.
        sku_level_items = [
            item for item in items if item.property_id != primary.property_id and is_varying(item)
        ]
        if len(sku_level_items) > 2:
            raise SheinConfiguratorAttributesLimitError(
                "Shein supports at most three sales attributes in total (one SKC-level, up to two SKU-level)."
            )
        return primary, sku_level_items

    def _build_sale_attribute_sort_list(self) -> list[dict[str, Any]]:
        if not self._supports_sale_attribute_sort() or not self.local_instance.is_configurable():
            return []

        configurator_items = list(self._get_configurator_rule_items())
        if not configurator_items:
            return []

        variations = list(self.local_instance.get_configurable_variations(active_only=True))
        if not variations:
            return []

        property_ids = {item.property_id for item in configurator_items}
        variation_properties = self._prefetch_variation_properties(
            variations=variations,
            property_ids=property_ids,
            relevant_only=True,
        )

        sorted_items = sorted(configurator_items, key=lambda item: getattr(item, "sort_order", 0))
        sort_entries: list[dict[str, Any]] = []

        for item in sorted_items:
            seen: dict[Any, ProductProperty] = {}
            for props in variation_properties.values():
                product_property = props.get(item.property_id)
                if product_property is None:
                    continue
                serialized = self._serialize_property_value(product_property=product_property)
                if serialized is None:
                    continue
                if serialized not in seen:
                    seen[serialized] = product_property

            if not seen:
                continue

            def sort_key(pair: tuple[Any, ProductProperty]):
                prop = pair[1]
                prop_type = prop.property.type
                if prop_type == Property.TYPES.SELECT:
                    return prop.value_select_id or 0
                if prop_type == Property.TYPES.MULTISELECT:
                    return tuple(sorted(prop.value_multi_select.values_list("id", flat=True)))
                value = prop.get_value()
                return str(value) if value is not None else ""

            payloads: list[dict[str, Any]] = []
            for _, product_property in sorted(seen.items(), key=sort_key):
                payload = self._build_sale_attribute_payload(product_property=product_property)
                if payload:
                    payloads.append(payload)

            if not payloads:
                continue

            attribute_id = payloads[0].get("attribute_id")
            if not attribute_id:
                continue

            has_custom = any(
                payload.get("custom_attribute_value") or payload.get("attribute_extra_value")
                for payload in payloads
            )
            if has_custom:
                in_order_list: list[dict[str, Any]] = []
                for payload in payloads:
                    entry: dict[str, Any] = {}
                    if payload.get("attribute_value_id") not in (None, "", []):
                        entry["attribute_value_id"] = payload.get("attribute_value_id")
                    if payload.get("custom_attribute_value") not in (None, "", []):
                        entry["custom_attribute_value"] = payload.get("custom_attribute_value")
                    if entry:
                        in_order_list.append(entry)
                if not in_order_list:
                    continue
                sort_entries.append(
                    {
                        "attribute_id": attribute_id,
                        "in_order_attribute_value_list": in_order_list,
                    }
                )
            else:
                id_list = [
                    payload.get("attribute_value_id")
                    for payload in payloads
                    if payload.get("attribute_value_id") not in (None, "", [])
                ]
                if not id_list:
                    continue
                sort_entries.append(
                    {
                        "attribute_id": attribute_id,
                        "in_order_attribute_value_id_list": id_list,
                    }
                )

        return sort_entries

    def _build_sku_list(
        self,
        *,
        assigns: list[SalesChannelViewAssign],
        product=None,
        sale_attributes: Optional[list[dict[str, Any]]] = None,
        sku_code: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if sale_attributes and len(sale_attributes) > 2:
            raise SheinConfiguratorAttributesLimitError(
                "Shein supports at most two SKU-level sales attributes per SKU."
            )
        use_create_payload = self._use_create_payload()
        price_info_list = (
            self._build_sku_price_info_list(assigns=assigns, product=product)
            if use_create_payload
            else []
        )
        stock_info_list = self._build_stock_info_list(assigns=assigns) if use_create_payload else []
        sku_sale_attributes = sale_attributes if use_create_payload else None
        product = product or self.local_instance
        height, length, width, weight = self._resolve_dimensions(product=product)
        supplier_barcode = self._build_supplier_barcode(product=product)
        package_type = self._get_internal_property_option_value(code="package_type", product=product)
        supplier_code = self._resolve_supplier_code(product=product, required=True)
        quantity_info = self._build_quantity_info(product=product)
        if quantity_info:
            self.has_quantity_info = True

        sku_entry: dict[str, Any] = {
            "mall_state": 1 if product.active else 2,
            "supplier_sku": product.sku,
            "supplier_code": supplier_code,
            "stop_purchase": 1,
            "height": height,
            "length": length,
            "width": width,
            "weight": weight,
            "quantity_info": quantity_info,
            "supplier_barcode": supplier_barcode,
            "package_type": package_type,
            "price_info_list": price_info_list or None,
            "sale_attribute_list": sku_sale_attributes or None,
            "stock_info_list": stock_info_list or None,
        }
        if not use_create_payload and sku_code:
            sku_entry["sku_code"] = sku_code
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
        remote_variations: dict[int, SheinProduct] = {}
        remote_variations_by_sku: dict[str, SheinProduct] = {}
        use_create_payload = self._use_create_payload()
        if not use_create_payload and self.remote_instance and self.local_instance.is_configurable():
            remote_variations_qs = (
                self.remote_model_class.objects.filter(
                    remote_parent_product=self.remote_instance,
                    is_variation=True,
                )
                .only("local_instance_id", "skc_name", "sku_code", "remote_sku")
            )
            for remote_variation in remote_variations_qs:
                if remote_variation.local_instance_id:
                    remote_variations[remote_variation.local_instance_id] = remote_variation
                if getattr(remote_variation, "remote_sku", None):
                    remote_variations_by_sku[str(remote_variation.remote_sku)] = remote_variation

        if not self.local_instance.is_configurable():
            supplier_code = self._resolve_supplier_code(product=self.local_instance, required=True)
            skc_name = (
                getattr(self.remote_instance, "skc_name", None)
                if (self.remote_instance and not use_create_payload)
                else None
            )
            sku_code = (
                getattr(self.remote_instance, "sku_code", None)
                if (self.remote_instance and not use_create_payload)
                else None
            )
            skc_entry: dict[str, Any] = {
                "shelf_way": "1",
                "image_info": (self.image_info or None) if include_skc_images else None,
                "sale_attribute": self.sale_attribute,
                "supplier_code": supplier_code,
                "sku_list": self._build_sku_list(assigns=assigns, sku_code=sku_code),
            }
            if skc_name:
                skc_entry["skc_name"] = skc_name

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
            relevant_only=True,
        )
        varying_map = self._collect_configurator_values(
            variation_properties=variation_properties,
            property_ids=property_ids,
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
            primary_variation = skc_variations[0] if skc_variations else None
            supplier_code = (
                self._resolve_supplier_code(product=primary_variation, required=True)
                if primary_variation is not None
                else None
            )

            sku_entries: list[dict[str, Any]] = []
            skc_name: Optional[str] = None
            for variation in skc_variations:
                remote_variation = remote_variations.get(variation.id) or remote_variations_by_sku.get(variation.sku)
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

                if skc_name is None and remote_variation is not None:
                    skc_name = getattr(remote_variation, "skc_name", None)

                sku_entries.extend(
                    self._build_sku_list(
                        assigns=assigns,
                        product=variation,
                        sale_attributes=sku_sale_attributes or None,
                        sku_code=getattr(remote_variation, "sku_code", None) if remote_variation else None,
                    )
                )

            skc_image_info = {}
            if include_skc_images and primary_variation is not None:
                primary_remote = (
                    remote_variations.get(primary_variation.id)
                    or remote_variations_by_sku.get(primary_variation.sku)
                    or self.remote_instance
                )
                skc_image_info = self._build_image_info_for_product(
                    product=primary_variation,
                    remote_product=primary_remote,
                )

            skc_entry: dict[str, Any] = {
                "shelf_way": "1",
                "image_info": (skc_image_info or None) if include_skc_images else None,
                "sale_attribute": sale_attribute,
                "supplier_code": supplier_code,
                "sku_list": sku_entries,
            }
            if skc_name:
                skc_entry["skc_name"] = skc_name

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
        self.sale_attribute_sort_list = self._build_sale_attribute_sort_list()

        use_create_payload = self._use_create_payload()
        self.site_list = self.build_site_list(product=self.local_instance) if use_create_payload else []
        package_type = self._get_internal_property_option_value(code="package_type")
        fill_configuration_info = self._build_fill_configuration_info(
            package_type=package_type,
            filled_quantity_to_sku=self.has_quantity_info,
        )
        supplier_code = (
            self._resolve_supplier_code(product=self.local_instance, required=False)
            if not self.local_instance.is_configurable()
            else None
        )

        brand_code = self._get_internal_property_option_value(code="brand_code")
        if brand_code in (None, "", []) and not use_create_payload:
            brand_code = ""

        competing_product_link = self._get_internal_property_value(
            code="reference_product_link",
            default=None,
        )
        if competing_product_link in (None, "", []):
            competing_product_link = None

        sale_attribute_list = self.sale_attribute_list if use_create_payload else None

        self.payload: dict[str, Any] = {
            "category_id": self.selected_category_id,
            "product_type_id": self.selected_product_type_id,
            "brand_code": brand_code,
            "competing_product_link": competing_product_link,
            "supplier_code": supplier_code,
            "source_system": "openapi",
            "site_list": self.site_list or None,
            "multi_language_name_list": self.multi_language_name_list or None,
            "multi_language_desc_list": self.multi_language_desc_list or None,
            "is_spu_pic": True if getattr(self, "use_spu_pic", False) else None,
            "image_info": (self.image_info or None) if getattr(self, "use_spu_pic", False) else None,
            "sale_attribute": self.sale_attribute,
            "sale_attribute_list": sale_attribute_list or None,
            "sale_attribute_sort_list": self.sale_attribute_sort_list or None,
            "size_attribute_list": self.size_attribute_list or None,
            "product_attribute_list": self.product_attribute_list or None,
            "skc_list": self.skc_list or None,
            "fill_configuration_info": fill_configuration_info,
        }
        if not use_create_payload:
            self.payload["spu_name"] = getattr(self.remote_instance, "remote_id", "") or ""
        # Clean None entries
        self.payload = {k: v for k, v in self.payload.items() if v not in (None, [], {})}

        if not use_create_payload:
            image_info = self.payload.get("image_info")
            if isinstance(image_info, dict) and image_info.get("image_info_list"):
                if not image_info.get("image_group_code"):
                    raise PreFlightCheckError(
                        "Shein image_group_code is required for editing images. "
                        "Sync the product details to populate image group codes."
                    )
            for skc in self.payload.get("skc_list") or []:
                if not isinstance(skc, dict):
                    continue
                skc_images = skc.get("image_info")
                if isinstance(skc_images, dict) and skc_images.get("image_info_list"):
                    if not skc_images.get("image_group_code"):
                        raise PreFlightCheckError(
                            "Shein image_group_code is required for editing SKC images. "
                            "Sync the product details to populate image group codes."
                        )
        return self.payload

    # ------------------------------------------------------------------
    # Remote actions
    # ------------------------------------------------------------------
    def perform_remote_action(self):
        self.value = getattr(self, "payload", {})
        if self.get_value_only:
            return self.value

        response = self.shein_post(
            path=self.publish_or_edit_path,
            payload=self.value,
        )
        response_data = response.json() if hasattr(response, "json") else {}

        logger.info(
            "Shein publish/edit response data: payload=%s response=%s",
            self.payload,
            response_data,
        )

        if isinstance(response_data, dict):
            code = response_data.get("code")
            msg = (response_data.get("msg") or "").strip()
            info = response_data.get("info")

            is_ok_code = code in ("0", 0)

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

            # Successful publish/edit responses can still include warnings in msg/filtered_result.
            # Treat code=0 together with info.success != False as success and continue persisting
            # the returned SPU/SKC/SKU identifiers.
            if not is_ok_code:
                raise SheinResponseException(msg or f"Shein API returned error code {code}.")


        self.set_remote_id(response_data)
        self._log_submission_tracking(response_data=response_data)
        self._update_or_create_remote_variations(response_data=response_data)
        if not self.is_create and self.remote_instance:
            self.remote_instance.status = self.remote_instance.STATUS_PENDING_APPROVAL
            self.remote_instance.save(update_fields=["status"], skip_status_check=False)
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

    def _extract_publish_response_identifiers(self, *, response_data: Any) -> dict[str, str]:
        if not isinstance(response_data, dict):
            return {}

        info = response_data.get("info") if isinstance(response_data.get("info"), dict) else response_data
        if not isinstance(info, dict):
            return {}

        spu_name = str(info.get("spu_name") or info.get("spuName") or "").strip()
        skc_list = info.get("skc_list") or info.get("skcList") or []

        skc_name = ""
        sku_code = ""
        if isinstance(skc_list, list) and skc_list:
            first_skc = skc_list[0] if isinstance(skc_list[0], dict) else {}
            skc_name = str(first_skc.get("skc_name") or first_skc.get("skcName") or "").strip()
            sku_list = first_skc.get("sku_list") or first_skc.get("skuList") or []
            if isinstance(sku_list, list) and sku_list:
                first_sku = sku_list[0] if isinstance(sku_list[0], dict) else {}
                sku_code = str(first_sku.get("sku_code") or first_sku.get("skuCode") or "").strip()

        return {
            "spu_name": spu_name,
            "skc_name": skc_name,
            "sku_code": sku_code,
        }

    def _persist_publish_response_identifiers(self, *, response_data: Any) -> None:
        if not self.remote_instance:
            return

        identifiers = self._extract_publish_response_identifiers(response_data=response_data)
        if not identifiers:
            return

        update_fields: set[str] = set()
        spu_name = identifiers.get("spu_name", "")
        skc_name = identifiers.get("skc_name", "")
        sku_code = identifiers.get("sku_code", "")

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

        if update_fields:
            self.remote_instance.save(update_fields=list(update_fields))

    def _update_or_create_remote_variations(self, *, response_data: Any) -> None:
        if not self.local_instance.is_configurable():
            return
        if not isinstance(response_data, dict) or not self.remote_instance:
            return

        info = response_data.get("info") if isinstance(response_data.get("info"), dict) else response_data
        if not isinstance(info, dict):
            return

        spu_name = str(
            info.get("spu_name")
            or info.get("spuName")
            or getattr(self.remote_instance, "spu_name", "")
            or ""
        ).strip()
        skc_list = info.get("skc_list") or info.get("skcList") or []
        if not skc_list:
            return

        variations = {variation.sku: variation for variation in self.local_instance.get_configurable_variations(active_only=True)}

        for skc in skc_list:
            if not isinstance(skc, dict):
                continue
            skc_name = str(skc.get("skc_name") or skc.get("skcName") or "").strip()
            for sku_entry in (skc.get("sku_list") or skc.get("skuList") or []):
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

    fixing_identifier_class = SheinProductBaseFactory
    action_log = RemoteLog.ACTION_UPDATE
    edit_permission_path = "/open-api/goods/product/check-edit-permission"

    def check_status(self, *, remote_product=None):
        super().check_status(remote_product=remote_product)
        if self.skip_checks or self.get_value_only:
            return

        remote_product = remote_product or getattr(self, "remote_product", None)
        if remote_product is None:
            return

        spu_name = (
            getattr(remote_product, "spu_name", None)
            or getattr(remote_product, "remote_id", None)
        )
        if not spu_name:
            return

        try:
            response = self.shein_post(
                path=self.edit_permission_path,
                payload={"spuName": spu_name},
            )
            data = response.json() if hasattr(response, "json") else {}
        except Exception:
            return

        info = data.get("info") if isinstance(data, dict) else {}
        if not isinstance(info, dict):
            return

        if info.get("editable", True):
            return

        reason = str(info.get("reason") or "").strip()
        message = (
            reason
            or "This product cannot be edited right now because it is still under review on Shein."
        )
        raise SkipSyncBecauseOfStatusException(message)

    def post_action_process(self):
        # @TODO: Basically this will never work because the update wil add the product to review and then we cannot do any
        # updates not ven with price update endpoint
        # price updates needs to be live in order to work not within the update product factory
        return
        self._update_prices()

    def _resolve_price_assigns(self) -> list[SalesChannelViewAssign]:
        assigns = list(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=self.local_instance,
            ).select_related("sales_channel_view")
        )
        if assigns:
            return assigns

        parent_product = getattr(self, "parent_local_instance", None)
        if parent_product is None:
            return []

        return list(
            SalesChannelViewAssign.objects.filter(
                sales_channel=self.sales_channel,
                product=parent_product,
            ).select_related("sales_channel_view")
        )

    def _resolve_variation_price_targets(self) -> list[tuple[Any, SheinProduct]]:
        variations = getattr(self, "variations", None)
        if variations is None:
            variations = self.local_instance.get_configurable_variations(active_only=True)
        variation_ids = list(variations.values_list("id", flat=True))
        if not variation_ids:
            return []

        remote_variations = list(
            self.remote_model_class.objects.filter(
                sales_channel=self.sales_channel,
                remote_parent_product=self.remote_instance,
                is_variation=True,
                local_instance_id__in=variation_ids,
            ).select_related("local_instance")
        )
        remote_by_local_id = {remote.local_instance_id: remote for remote in remote_variations}

        targets: list[tuple[Any, SheinProduct]] = []
        for variation in variations:
            remote_variation = remote_by_local_id.get(variation.id)
            if remote_variation is None:
                continue
            targets.append((variation, remote_variation))

        return targets

    def _should_update_prices(self) -> bool:
        if self.get_value_only or self.skip_checks:
            return False
        if self.skip_price_update:
            return False
        if not getattr(self.sales_channel, "sync_prices", False):
            return False
        if self.local_instance.is_configurable() and not getattr(self, "is_variation", False):
            return True
        if not getattr(self.remote_instance, "sku_code", None):
            return False
        return True

    def _update_prices(self) -> None:
        if not self._should_update_prices():
            return

        if self.local_instance.is_configurable() and not getattr(self, "is_variation", False):
            price_assigns = self._resolve_price_assigns()
            for variation, remote_variation in self._resolve_variation_price_targets():
                if not getattr(remote_variation, "sku_code", None):
                    continue
                price_factory = SheinPriceUpdateFactory(
                    sales_channel=self.sales_channel,
                    local_instance=variation,
                    remote_product=remote_variation,
                    get_value_only=False,
                    skip_checks=False,
                    assigns=price_assigns or None,
                    use_remote_prices=True,
                )
                price_factory.run()
            return

        assigns = self._resolve_price_assigns()
        price_factory = SheinPriceUpdateFactory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_instance,
            get_value_only=False,
            skip_checks=False,
            assigns=assigns or None,
            use_remote_prices=True,
        )
        price_factory.run()

    def update_multi_currency_prices(self):  # type: ignore[override]
        """Update handled explicitly for edits; avoid duplicate runs from the base hook."""
        return

    def update_remote(self):
        return self.perform_remote_action()

    def set_remote_id(self, response_data):
        self._persist_publish_response_identifiers(response_data=response_data)


class SheinProductCreateFactory(SheinProductBaseFactory, RemoteProductCreateFactory):
    """Create a Shein product or fall back to sync."""

    fixing_identifier_class = SheinProductBaseFactory
    action_log = RemoteLog.ACTION_CREATE
    sync_product_factory = SheinProductUpdateFactory
    remote_price_class = SheinPrice
    remote_product_content_class = SheinProductContent

    def run_sync_flow(self):
        """Run update flow preserving create-time runtime flags."""
        if self.sync_product_factory is None:
            raise ValueError("sync_product_factory must be specified in the RemoteProductCreateFactory.")

        sync_factory = self.sync_product_factory(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_instance=self.remote_instance,
            parent_local_instance=self.parent_local_instance,
            remote_parent_product=self.remote_parent_product,
            api=self.api,
            is_switched=True,
            get_value_only=self.get_value_only,
            skip_checks=self.skip_checks,
            skip_price_update=self.skip_price_update,
            skip_property_values_category_validation=self.skip_property_values_category_validation,
        )
        sync_factory.run()

    def create_remote(self):
        return self.perform_remote_action()

    def set_remote_id(self, response_data):
        self._persist_publish_response_identifiers(response_data=response_data)

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

    def get_delete_product_factory(self):
        return SheinProductDeleteFactory

    remote_delete_factory = property(get_delete_product_factory)

    def get_api(self):
        return getattr(self, "api", None)

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

    @staticmethod
    def _extract_revoke_fail_messages(*, payload: dict[str, Any]) -> list[str]:
        info = payload.get("info")
        if not isinstance(info, dict):
            return []

        fail_list = info.get("failList")
        if not isinstance(fail_list, list):
            fail_list = []

        fail_messages: list[str] = []
        for item in fail_list:
            if not isinstance(item, dict):
                continue
            message = str(item.get("msg") or "").strip() or "Unknown revoke failure"
            document_sn = str(item.get("documentSn") or "").strip()
            skc_name = str(item.get("skcName") or "").strip()
            details: list[str] = []
            if document_sn:
                details.append(f"documentSn={document_sn}")
            if skc_name:
                details.append(f"skcName={skc_name}")
            if details:
                fail_messages.append(f"{message} ({', '.join(details)})")
            else:
                fail_messages.append(message)

        fail_count_raw = info.get("failCount")
        try:
            fail_count = int(fail_count_raw or 0)
        except (TypeError, ValueError):
            fail_count = 0

        if fail_count > 0 and not fail_messages:
            fail_messages.append(f"Shein revoke returned failCount={fail_count}.")

        return fail_messages

    def delete_remote(self):
        spu_name = getattr(self.remote_instance, "remote_id", None)
        if not spu_name:
            return {}

        response = self.shein_post(
            path=self.revoke_path,
            payload={"spuName": spu_name},
        )
        payload = self._extract_successful_shein_json(
            response=response,
            context="product revoke",
        )

        fail_messages = self._extract_revoke_fail_messages(payload=payload)
        if fail_messages:
            raise SheinResponseException(
                "Shein product revoke failed: " + "; ".join(fail_messages)
            )
        return payload
