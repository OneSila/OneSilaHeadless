from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional

from django.db import IntegrityError

from sales_channels.factories.products.products import RemoteProductSyncFactory
from properties.models import ProductProperty
from products.models import ConfigurableVariation

from sales_channels.integrations.ebay.factories.products.content import (
    EbayProductContentUpdateFactory,
)
from sales_channels.integrations.ebay.factories.products.eancodes import (
    EbayEanCodeUpdateFactory,
)
from sales_channels.integrations.ebay.factories.products.images import (
    EbayMediaProductThroughCreateFactory,
    EbayMediaProductThroughDeleteFactory,
    EbayMediaProductThroughUpdateFactory,
)
from sales_channels.integrations.ebay.factories.products.mixins import (
    EbayInventoryItemPushMixin,
)
from sales_channels.integrations.ebay.exceptions import (
    EbayMissingListingPoliciesError,
    EbayMissingProductMappingError,
    EbayMissingVariationMappingsError,
    EbayResponseException,
)
from sales_channels.integrations.ebay.factories.products.properties import (
    EbayProductPropertyCreateFactory,
    EbayProductPropertyDeleteFactory,
    EbayProductPropertyUpdateFactory,
)
from sales_channels.integrations.ebay.factories.prices import EbayPriceUpdateFactory
from sales_channels.integrations.ebay.models.products import (
    EbayPrice,
    EbayProduct,
    EbayProductContent,
)
from sales_channels.integrations.ebay.models.properties import (
    EbayProductProperty,
    EbayInternalProperty,
    EbayProperty,
)


logger = logging.getLogger(__name__)


class EbayProductBaseFactory(EbayInventoryItemPushMixin, RemoteProductSyncFactory):
    """Common helpers for single-SKU eBay product factories."""

    remote_model_class = EbayProduct
    remote_image_assign_create_factory = EbayMediaProductThroughCreateFactory
    remote_image_assign_update_factory = EbayMediaProductThroughUpdateFactory
    remote_image_assign_delete_factory = EbayMediaProductThroughDeleteFactory

    remote_product_property_class = EbayProductProperty
    remote_product_property_create_factory = EbayProductPropertyCreateFactory
    remote_product_property_update_factory = EbayProductPropertyUpdateFactory
    remote_product_property_delete_factory = EbayProductPropertyDeleteFactory

    remote_price_update_factory = EbayPriceUpdateFactory
    remote_eancode_update_factory = EbayEanCodeUpdateFactory
    remote_product_content_update_factory = EbayProductContentUpdateFactory

    def __init__(
        self,
        *,
        sales_channel,
        local_instance,
        view,
        api=None,
        remote_instance=None,
        get_value_only: bool = False,
        enable_price_update: bool = True,
        **kwargs: Any,
    ) -> None:
        self.view = view
        self.get_value_only = get_value_only
        self._enable_price_update = enable_price_update
        super().__init__(
            sales_channel=sales_channel,
            local_instance=local_instance,
            api=api,
            remote_instance=remote_instance,
            view=view,
            get_value_only=get_value_only,
            **kwargs,
        )
        self.remote_product = remote_instance

        # Ensure create/update factories share the same fixing identifier for log retries.
        type(self).fixing_identifier_class = EbayProductBaseFactory

    def get_identifiers(self, *, fixing_caller: str = "run"):
        frame = inspect.currentframe()
        caller = frame.f_back.f_code.co_name
        class_name = EbayProductBaseFactory.__name__

        fixing_class = getattr(self, "fixing_identifier_class", None)
        fixing_identifier = None
        if fixing_caller and fixing_class:
            fixing_identifier = f"{fixing_class.__name__}:{fixing_caller}"

        return f"{class_name}:{caller}", fixing_identifier

    # ------------------------------------------------------------------
    # Base utilities
    # ------------------------------------------------------------------
    def preflight_check(self) -> bool:
        return self.view is not None and super().preflight_check()

    def validate(self) -> None:
        if getattr(self, "skip_checks", False):
            return

        super().validate()

        from sales_channels.integrations.ebay.models import (
            EbayProductCategory,
            EbayProductType,
        )

        view = self.view
        product = self.local_instance

        fulfillment_id = getattr(view, "fulfillment_policy_id", None)
        payment_id = getattr(view, "payment_policy_id", None)
        return_id = getattr(view, "return_policy_id", None)

        missing = []
        if not fulfillment_id:
            missing.append("fulfillment policy")
        if not payment_id:
            missing.append("payment policy")
        if not return_id:
            missing.append("return policy")

        if missing:
            raise EbayMissingListingPoliciesError(
                "Missing eBay listing policies ({}). Please configure the marketplace policies before pushing products.".format(
                    ", ".join(missing)
                )
            )

        product_rule = product.get_product_rule(sales_channel=self.sales_channel)
        has_type_mapping = False
        if product_rule:
            has_type_mapping = EbayProductType.objects.filter(
                local_instance=product_rule,
                marketplace=view,
            ).exists()

        def has_required_ebay_mapping(target):
            if has_type_mapping:
                return True

            return EbayProductCategory.objects.filter(
                product=target,
                view=view,
            ).exists()

        if product.is_configurable():
            variations = product.get_configurable_variations(active_only=True)
            missing_skus = [
                variation.sku or str(variation.pk)
                for variation in variations
                if not has_required_ebay_mapping(variation)
            ]

            if missing_skus:
                raise EbayMissingVariationMappingsError(
                    "eBay configurable products require each variation to have either a mapped product type or a category assigned. Missing for SKU(s): {}.".format(
                        ", ".join(missing_skus)
                    )
                )
        else:
            if not has_required_ebay_mapping(product):
                raise EbayMissingProductMappingError(
                    "Before listing on eBay, assign either a mapped product type or a category to this product."
                )

    def set_api(self) -> None:
        if self.get_value_only:
            return
        if getattr(self, "api", None) is None:
            self.api = self.get_api()

    def _is_configurable_product(self) -> bool:
        product = self.local_instance
        return bool(product and hasattr(product, "is_configurable") and product.is_configurable())

    def _collect_child_remote_products(self) -> List[EbayProduct]:
        if not self._is_configurable_product():
            return []

        parent_remote = getattr(self, "remote_product", None)
        if parent_remote is None:
            return []

        child_mappings = ConfigurableVariation.objects.filter(parent=self.local_instance).select_related("variation")
        remote_children: List[EbayProduct] = []

        for mapping in child_mappings:
            child = getattr(mapping, "variation", None)
            if child is None:
                continue

            remote_child = EbayProduct.objects.filter(
                local_instance=child,
                sales_channel=self.sales_channel,
            ).first()

            sku = child.sku
            if remote_child is not None:
                sku = remote_child.remote_sku or remote_child.remote_id or sku

            if remote_child is None:
                try:
                    remote_child = EbayProduct.objects.create(
                        multi_tenant_company=self.sales_channel.multi_tenant_company,
                        sales_channel=self.sales_channel,
                        local_instance=child,
                        remote_parent_product=parent_remote,
                        remote_sku=sku,
                        remote_id=sku,
                        is_variation=True,
                    )
                except IntegrityError:
                    remote_child = EbayProduct.objects.filter(
                        sales_channel=self.sales_channel,
                        remote_sku=sku,
                        remote_parent_product=parent_remote,
                    ).first()
                    if remote_child is None:
                        raise
            else:
                updates: list[str] = []
                if remote_child.remote_parent_product_id != parent_remote.id:
                    remote_child.remote_parent_product = parent_remote
                    updates.append("remote_parent_product")
                if remote_child.remote_sku != sku:
                    remote_child.remote_sku = sku
                    updates.append("remote_sku")
                if remote_child.remote_id != sku:
                    remote_child.remote_id = sku
                    if "remote_id" not in updates:
                        updates.append("remote_id")
                if not remote_child.is_variation:
                    remote_child.is_variation = True
                    updates.append("is_variation")
                if updates:
                    self._update_remote_product_fields(
                        remote_product=remote_child,
                        fields=tuple(updates),
                    )

            self._ensure_offer_for_remote(remote_product=remote_child)
            remote_children.append(remote_child)

        return remote_children

    def _get_remote_child_sku(self, *, remote_product: EbayProduct) -> str:
        sku = (
            getattr(remote_product, "remote_sku", None)
            or getattr(remote_product, "remote_id", None)
            or getattr(getattr(remote_product, "local_instance", None), "sku", None)
        )
        normalized_sku = str(sku).strip() if sku not in (None, "") else ""
        if not normalized_sku:
            raise EbayResponseException(
                "Unable to recover configurable variation mismatch because the variation SKU could not be resolved."
            )
        return normalized_sku

    @staticmethod
    def _get_first_mapping_value(
        *,
        payload: Mapping[str, Any],
        keys: Sequence[str],
    ) -> Any:
        for key in keys:
            if key in payload:
                return payload.get(key)
        return None

    @staticmethod
    def _normalize_single_aspect_value(*, raw_value: Any) -> str:
        if isinstance(raw_value, Sequence) and not isinstance(raw_value, (str, bytes)):
            for value in raw_value:
                if value in (None, ""):
                    continue
                normalized = str(value).strip()
                if normalized:
                    return normalized
            return ""

        if raw_value in (None, ""):
            return ""

        return str(raw_value).strip()

    def _fetch_inventory_group_payload_from_server(self) -> Mapping[str, Any]:
        group_key = self.get_parent_remote_sku()
        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        try:
            payload = api.sell_inventory_get_inventory_item_group(
                inventory_item_group_key=group_key,
            )
        except Exception as exc:
            raise EbayResponseException(
                f"Unable to fetch inventory item group {group_key} for configurable mismatch recovery: {exc}"
            ) from exc

        if not isinstance(payload, Mapping):
            raise EbayResponseException(
                f"Invalid inventory item group payload received from eBay for group {group_key}."
            )

        return payload

    def _fetch_inventory_item_payload_from_server(self, *, sku: str) -> Mapping[str, Any]:
        api = getattr(self, "api", None) or self.get_api()
        self.api = api
        try:
            payload = api.sell_inventory_get_inventory_item(sku=sku)
        except Exception as exc:
            raise EbayResponseException(
                f"Unable to fetch inventory item {sku} for configurable mismatch recovery: {exc}"
            ) from exc

        if not isinstance(payload, Mapping):
            raise EbayResponseException(
                f"Invalid inventory item payload received from eBay for SKU {sku}."
            )

        return payload

    def _extract_variation_aspect_names_from_group_payload(
        self,
        *,
        group_payload: Mapping[str, Any],
    ) -> List[str]:
        varies_by = self._get_first_mapping_value(
            payload=group_payload,
            keys=("variesBy", "varies_by"),
        )
        if not isinstance(varies_by, Mapping):
            return []

        names: List[str] = []
        specifications = varies_by.get("specifications")
        if isinstance(specifications, Sequence) and not isinstance(specifications, (str, bytes)):
            for specification in specifications:
                if not isinstance(specification, Mapping):
                    continue
                name = specification.get("name")
                if name in (None, ""):
                    continue
                normalized = str(name).strip()
                if normalized and normalized not in names:
                    names.append(normalized)

        if names:
            return names

        # Fallback only when specifications are missing/empty.
        image_varies_by = self._get_first_mapping_value(
            payload=varies_by,
            keys=("aspectsImageVariesBy", "aspects_image_varies_by"),
        )
        if not isinstance(image_varies_by, Sequence) or isinstance(image_varies_by, (str, bytes)):
            return []

        for value in image_varies_by:
            if value in (None, ""):
                continue
            normalized = str(value).strip()
            if normalized and normalized not in names:
                names.append(normalized)

        return names

    def _extract_group_variant_skus_from_payload(
        self,
        *,
        group_payload: Mapping[str, Any],
    ) -> List[str]:
        raw_variant_skus = self._get_first_mapping_value(
            payload=group_payload,
            keys=("variantSKUs", "variant_skus"),
        )
        if not isinstance(raw_variant_skus, Sequence) or isinstance(raw_variant_skus, (str, bytes)):
            return []

        variant_skus: List[str] = []
        for sku in raw_variant_skus:
            if sku in (None, ""):
                continue
            normalized = str(sku).strip()
            if normalized:
                variant_skus.append(normalized)

        return variant_skus

    def _extract_sku_variation_state_from_inventory_item(
        self,
        *,
        sku: str,
        inventory_item_payload: Mapping[str, Any],
        aspect_names: Sequence[str],
    ) -> Dict[str, str]:
        product_payload = inventory_item_payload.get("product")
        if not isinstance(product_payload, Mapping):
            raise EbayResponseException(
                f"Inventory item {sku} is missing product payload while recovering configurable mismatch."
            )

        aspects_payload = product_payload.get("aspects")
        if not isinstance(aspects_payload, Mapping):
            raise EbayResponseException(
                f"Inventory item {sku} is missing product aspects while recovering configurable mismatch."
            )

        casefold_aspects = {
            str(key).strip().lower(): value
            for key, value in aspects_payload.items()
            if key not in (None, "")
        }

        state: Dict[str, str] = {}
        for aspect_name in list(aspect_names):
            normalized_name = str(aspect_name).strip()
            if not normalized_name:
                continue

            raw_value = aspects_payload.get(normalized_name)
            if raw_value is None:
                raw_value = casefold_aspects.get(normalized_name.lower())

            value = self._normalize_single_aspect_value(raw_value=raw_value)
            if not value:
                raise EbayResponseException(
                    f"Inventory item {sku} is missing variation value for aspect '{normalized_name}' while recovering configurable mismatch."
                )

            state[normalized_name] = value

        return state

    def _build_variants_override_from_server_state(
        self,
        *,
        sku_variation_state: Mapping[str, Mapping[str, str]],
        aspect_names: Sequence[str],
    ) -> tuple[List[str], List[Dict[str, Any]]]:
        variant_skus: List[str] = []
        collected_values: Dict[str, List[str]] = {
            str(aspect_name).strip(): []
            for aspect_name in list(aspect_names)
            if str(aspect_name).strip()
        }
        seen_values: Dict[str, set[str]] = {
            aspect_name: set()
            for aspect_name in collected_values
        }

        for sku, aspect_state in sku_variation_state.items():
            normalized_sku = str(sku).strip() if sku not in (None, "") else ""
            if not normalized_sku:
                continue

            variant_skus.append(normalized_sku)
            for aspect_name in collected_values:
                value = ""
                if isinstance(aspect_state, Mapping):
                    raw_value = aspect_state.get(aspect_name)
                    value = str(raw_value).strip() if raw_value not in (None, "") else ""
                if not value:
                    raise EbayResponseException(
                        f"Unable to build configurable variation override: missing value for SKU {normalized_sku} and aspect '{aspect_name}'."
                    )
                if value not in seen_values[aspect_name]:
                    seen_values[aspect_name].add(value)
                    collected_values[aspect_name].append(value)

        if not variant_skus:
            raise EbayResponseException(
                "Unable to build configurable variation override: no variant SKUs available."
            )

        specifications: List[Dict[str, Any]] = []
        for aspect_name, values in collected_values.items():
            if not values:
                raise EbayResponseException(
                    f"Unable to build configurable variation override: no values available for aspect '{aspect_name}'."
                )
            specifications.append({"name": aspect_name, "values": values})

        return variant_skus, specifications

    def _fetch_configurator_server_state(
        self,
    ) -> tuple[List[str], Dict[str, Dict[str, str]]]:
        group_payload = self._fetch_inventory_group_payload_from_server()
        aspect_names = self._extract_variation_aspect_names_from_group_payload(
            group_payload=group_payload,
        )
        if not aspect_names:
            raise EbayResponseException(
                "Unable to recover configurable variation mismatch because group variation dimensions could not be resolved from eBay."
            )

        variant_skus = self._extract_group_variant_skus_from_payload(
            group_payload=group_payload,
        )
        if not variant_skus:
            raise EbayResponseException(
                "Unable to recover configurable variation mismatch because group variation SKUs could not be resolved from eBay."
            )

        sku_variation_state: Dict[str, Dict[str, str]] = {}
        for sku in variant_skus:
            inventory_item_payload = self._fetch_inventory_item_payload_from_server(sku=sku)
            try:
                payload_dump = json.dumps(inventory_item_payload, indent=2, sort_keys=True, default=str)
            except TypeError:
                payload_dump = str(inventory_item_payload)
            logger.debug(
                "EBAY_CONFIG_MISMATCH_RECOVERY inventory_item_payload for SKU %s:\n%s",
                sku,
                payload_dump,
            )
            sku_variation_state[sku] = self._extract_sku_variation_state_from_inventory_item(
                sku=sku,
                inventory_item_payload=inventory_item_payload,
                aspect_names=aspect_names,
            )

        return aspect_names, sku_variation_state

    def _refresh_variation_state_for_sku(
        self,
        *,
        sku: str,
        aspect_names: Sequence[str],
    ) -> Dict[str, str]:
        inventory_item_payload = self._fetch_inventory_item_payload_from_server(sku=sku)
        return self._extract_sku_variation_state_from_inventory_item(
            sku=sku,
            inventory_item_payload=inventory_item_payload,
            aspect_names=aspect_names,
        )

    def _recover_configurator_variation_mismatch(
        self,
        *,
        remote_products: List[EbayProduct],
    ) -> List[Any]:
        if not remote_products:
            return []

        aspect_names, sku_variation_state = self._fetch_configurator_server_state()
        recovered_inventory_responses: List[Any] = []
        for remote_product in remote_products:
            target_sku = self._get_remote_child_sku(remote_product=remote_product)
            if target_sku not in sku_variation_state:
                raise EbayResponseException(
                    f"Unable to recover configurable variation mismatch because SKU {target_sku} is not present in the eBay inventory group state."
                )

            logger.warning(
                "Recovering eBay configurable variation mismatch for SKU %s with server-state variation overrides.",
                target_sku,
            )

            detached_variation_state = {
                sku: state
                for sku, state in sku_variation_state.items()
                if sku != target_sku
            }
            detached_variant_skus, detached_specifications = self._build_variants_override_from_server_state(
                sku_variation_state=detached_variation_state,
                aspect_names=aspect_names,
            )
            self.send_inventory_payload_with_variants_override(
                variant_skus=detached_variant_skus,
                specifications=detached_specifications,
            )

            with self._use_remote_product(remote_product):
                recovered_inventory_responses.append(self.send_inventory_payload())

            sku_variation_state[target_sku] = self._refresh_variation_state_for_sku(
                sku=target_sku,
                aspect_names=aspect_names,
            )
            attached_variant_skus, attached_specifications = self._build_variants_override_from_server_state(
                sku_variation_state=sku_variation_state,
                aspect_names=aspect_names,
            )
            self.send_inventory_payload_with_variants_override(
                variant_skus=attached_variant_skus,
                specifications=attached_specifications,
            )

        return recovered_inventory_responses

    def _run_configurable_sequence(self) -> Dict[str, Any]:
        self._build_listing_policies()
        child_remotes = self._collect_child_remote_products()
        inventory_responses, error_configurator_remote_products = self.send_bulk_inventory_payloads(
            remote_products=child_remotes,
        )
        if error_configurator_remote_products:
            recovered_inventory_responses = self._recover_configurator_variation_mismatch(
                remote_products=error_configurator_remote_products,
            )
            inventory_responses.extend(recovered_inventory_responses)

        children_payloads = {
            "inventory": inventory_responses,
            "offers": self.send_bulk_offer_payloads(remote_products=child_remotes),
        }

        group_result = self.send_inventory_payload()
        publish_result = self.publish_group()
        extras = self._post_inventory_push()

        result: Dict[str, Any] = {
            "children": children_payloads,
            "group": group_result,
            "publish": publish_result,
        }
        if extras:
            result.update(extras)
        return result

    def _resolve_remote_product(self) -> EbayProduct:
        remote_product = getattr(self, "remote_instance", None)
        expected_parent = getattr(self, "remote_parent_product", None)

        if remote_product is None:
            filter_kwargs = {
                "local_instance": self.local_instance,
                "sales_channel": self.sales_channel,
            }
            if expected_parent is not None:
                filter_kwargs["remote_parent_product"] = expected_parent
            else:
                filter_kwargs["remote_parent_product__isnull"] = True
            remote_product = EbayProduct.objects.filter(**filter_kwargs).first()

        if expected_parent is None and remote_product is not None:
            expected_parent = remote_product.remote_parent_product

        created = False
        if remote_product is None:
            sku = self._get_sku(product=self.local_instance)
            remote_product = EbayProduct.objects.create(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=self.local_instance,
                remote_parent_product=expected_parent,
                remote_sku=sku,
                remote_id=sku,
                is_variation=expected_parent is not None,
            )
            created = True

        updates: list[str] = []
        sku = self._get_sku(product=self.local_instance)

        if remote_product.remote_sku != sku:
            remote_product.remote_sku = sku
            updates.append("remote_sku")

        if remote_product.remote_id != sku:
            remote_product.remote_id = sku
            if "remote_id" not in updates:
                updates.append("remote_id")

        if expected_parent is None and remote_product.remote_parent_product_id is not None:
            remote_product.remote_parent_product = None
            updates.append("remote_parent_product")
        elif (
            expected_parent is not None
            and remote_product.remote_parent_product_id != expected_parent.id
        ):
            remote_product.remote_parent_product = expected_parent
            updates.append("remote_parent_product")

        is_variation = expected_parent is not None
        if remote_product.is_variation != is_variation:
            remote_product.is_variation = is_variation
            updates.append("is_variation")

        if updates:
            self._update_remote_product_fields(
                remote_product=remote_product,
                fields=tuple(updates),
            )

        self.remote_product = remote_product
        self.remote_instance = remote_product
        self.remote_parent_product = expected_parent
        self._ensure_offer_record(remote_product=remote_product)
        self._ensure_content_price_mirrors(remote_product=remote_product)
        return remote_product

    def _ensure_content_price_mirrors(self, *, remote_product: EbayProduct) -> None:
        if not self.sales_channel.sync_contents:
            return
        content, _ = EbayProductContent.objects.get_or_create(
            remote_product=remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )
        from sales_channels.helpers import build_content_data, compute_content_data_hash

        content_data = build_content_data(
            product=self.local_instance,
            sales_channel=self.sales_channel,
        )
        content.content_data = content_data
        content.save()

        if not self.sales_channel.sync_prices:
            return

        price, _ = EbayPrice.objects.get_or_create(
            remote_product=remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )
        from sales_channels.helpers import build_price_data

        price.price_data = build_price_data(
            product=self.local_instance,
            sales_channel=self.sales_channel,
        )
        price.save()

    def _post_inventory_push(self) -> None:
        return {
            key: value
            for key, value in {
                "properties": self._sync_properties(),
                "content": self._trigger_content_update(),
                "price": self._trigger_price_update(),
                "ean": self._trigger_ean_update(),
            }.items()
            if value is not None
        }

    def _sync_properties(self) -> Dict[str, str] | None:
        if not self.remote_product_property_class:
            return None

        product_properties = (
            ProductProperty.objects.filter(product=self.local_instance)
            .select_related("property")
            .prefetch_related("value_multi_select")
        )

        if self.get_value_only:
            values: Dict[str, str] = {}
            language_code = self._get_language_code()
            internal_properties = {
                internal.local_instance_id: internal
                for internal in (
                    EbayInternalProperty.objects.filter(
                        sales_channel=self.sales_channel,
                        local_instance__isnull=False,
                    )
                    .select_related("local_instance")
                    .prefetch_related("options__local_instance")
                )
            }
            for product_property in product_properties:
                remote_property = EbayProperty.objects.filter(
                    sales_channel=self.sales_channel,
                    marketplace=self.view,
                    local_instance=product_property.property,
                ).first()
                if remote_property is None:
                    internal_property = internal_properties.get(product_property.property_id)
                    if internal_property is None:
                        continue
                    value = self._render_basic_property_value(
                        product_property=product_property,
                        language_code=language_code,
                    )
                    value = self._normalize_internal_property_value(
                        internal_property=internal_property,
                        product_property=product_property,
                        value=value,
                    )
                    if value in (None, "", []):
                        continue
                    if isinstance(value, (dict, list)):
                        values[str(product_property.property_id)] = json.dumps(
                            value,
                            sort_keys=True,
                        )
                    else:
                        values[str(product_property.property_id)] = str(value)
                    continue
                values[str(product_property.property_id)] = self._prepare_property_remote_value(
                    product_property=product_property,
                    remote_property=remote_property,
                )
            return values

        for product_property in product_properties:
            remote_property = EbayProperty.objects.filter(
                sales_channel=self.sales_channel,
                marketplace=self.view,
                local_instance=product_property.property,
            ).first()
            if remote_property is None:
                continue

            defaults: Dict[str, Any] = {
                "multi_tenant_company": self.sales_channel.multi_tenant_company,
            }
            if remote_property is not None:
                defaults["remote_property"] = remote_property

            remote_instance, created = self.remote_product_property_class.objects.get_or_create(
                remote_product=self.remote_product,
                sales_channel=self.sales_channel,
                local_instance=product_property,
                defaults=defaults,
            )

            updates: list[str] = []
            if (
                remote_property is not None
                and remote_instance.remote_property_id != remote_property.id
            ):
                remote_instance.remote_property = remote_property
                updates.append("remote_property")

            remote_value = self._prepare_property_remote_value(
                product_property=product_property,
                remote_property=remote_property,
            )
            if remote_instance.remote_value != remote_value:
                remote_instance.remote_value = remote_value
                updates.append("remote_value")

            if created and "remote_value" not in updates:
                remote_instance.remote_value = remote_value
                updates.append("remote_value")

            if updates:
                remote_instance.save(update_fields=updates)

        return None

    def _trigger_content_update(self) -> Any:
        factory_class = getattr(self, "remote_product_content_update_factory", None)
        if factory_class is None:
            return None

        if self.get_value_only:
            return {"listingDescription": self.get_listing_description()}

        remote_model = factory_class.remote_model_class
        remote_instance, _ = remote_model.objects.get_or_create(
            remote_product=self.remote_product,
            sales_channel=self.sales_channel,
            multi_tenant_company=self.sales_channel.multi_tenant_company,
        )
        factory = factory_class(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_product,
            remote_instance=remote_instance,
            api=self.api,
            view=self.view,
            get_value_only=self.get_value_only,
            skip_checks=True,
        )
        return factory.run()

    def _trigger_price_update(self) -> None:
        factory_class = getattr(self, "remote_price_update_factory", None)
        if factory_class is None:
            return None
        factory = factory_class(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_product,
            view=self.view,
            api=self.api,
            get_value_only=self.get_value_only,
        )

        primary_currency = self._get_primary_currency()
        if primary_currency is not None:
            factory.limit_to_currency_iso = primary_currency.iso_code

        factory.set_to_update_currencies()
        has_discount = any(
            (details.get("discount_price") not in (None, ""))
            for details in factory.price_data.values()
        )

        allow_price_update = getattr(self, "_enable_price_update", True) and not self.get_value_only
        factory.skip_price_update = not allow_price_update

        if not allow_price_update:
            factory.get_value_only = not has_discount

        result = factory.run()
        return getattr(factory, "value", None) or result

    def _trigger_ean_update(self) -> None:
        factory_class = getattr(self, "remote_eancode_update_factory", None)
        if factory_class is None:
            return None
        factory = factory_class(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_product=self.remote_product,
            view=self.view,
            api=self.api,
            get_value_only=self.get_value_only,
        )
        return factory.run()

    # ------------------------------------------------------------------
    # Flow helpers
    # ------------------------------------------------------------------
    def _run_offer_sequence(self) -> Dict[str, Any]:
        offer_response = self.send_offer()
        publish_response = self.publish_offer()
        return {
            "offer": offer_response,
            "publish": publish_response,
        }


class EbayProductCreateFactory(EbayProductBaseFactory):
    """Create the remote inventory item and marketplace offer for a product."""

    def __init__(self, *, enable_price_update: bool = False, **kwargs) -> None:
        super().__init__(enable_price_update=enable_price_update, **kwargs)

    def run(self) -> Optional[Dict[str, Any]]:
        run_succeeded = None
        if not self.preflight_check():
            return None

        self.set_api()
        self.set_type()
        log_identifier, fixing_identifier = self.get_identifiers()

        try:
            self._build_listing_policies()
            self._resolve_remote_product()
            self.set_remote_product_for_logging()
            self.validate()
            self.sanity_check()
            self.precalculate_progress_step_increment(3)
            self.update_progress()

            if self._is_configurable_product():
                result = self._run_configurable_sequence()
            else:
                inventory_result = self.send_inventory_payload()

                if self.get_value_only:
                    extras = self._post_inventory_push()
                    value_only: Dict[str, Any] = {
                        "inventory": inventory_result,
                        "offer": self.build_offer_payload(),
                    }
                    value_only.update(extras)
                    return value_only

                offer_data = self._run_offer_sequence()
                extras = self._post_inventory_push()

                result = {"inventory": inventory_result}
                result.update(offer_data)
                result.update(extras)

            self.update_progress()
            self.final_process()
            self.log_action(self.action_log, result or {}, self.payload, log_identifier)
            run_succeeded = True
            return result

        except Exception as exc:
            run_succeeded = False
            self.log_error(exc, self.action_log, log_identifier, self.payload, fixing_identifier)
            raise

        finally:
            if run_succeeded is False:
                self._set_successfully_created(value=False)
            elif run_succeeded is True:
                self._set_successfully_created(value=True)
            self.finalize_progress()


class EbayProductUpdateFactory(EbayProductBaseFactory):
    """Refresh inventory and offer data for an existing listing."""

    def run(self) -> Optional[Dict[str, Any]]:
        run_succeeded = None
        if not self.preflight_check():
            return None

        self.set_api()
        self.set_type()
        log_identifier, fixing_identifier = self.get_identifiers()

        try:
            self._build_listing_policies()
            self._resolve_remote_product()
            self.set_remote_product_for_logging()
            self.validate()
            self.sanity_check()
            self.precalculate_progress_step_increment(3)
            self.update_progress()

            if self._is_configurable_product():
                result = self._run_configurable_sequence()
            else:
                inventory_result = self.send_inventory_payload()

                if self.get_value_only:
                    extras = self._post_inventory_push()
                    value_only: Dict[str, Any] = {
                        "inventory": inventory_result,
                        "offer": self.build_offer_payload(),
                    }
                    value_only.update(extras)
                    return value_only

                offer_data = self._run_offer_sequence()
                extras = self._post_inventory_push()

                result = {"inventory": inventory_result}
                result.update(offer_data)
                result.update(extras)

            self.update_progress()
            self.final_process()
            self.log_action(self.action_log, result or {}, self.payload, log_identifier)
            run_succeeded = True
            return result

        except Exception as exc:
            run_succeeded = False
            self.log_error(exc, self.action_log, log_identifier, self.payload, fixing_identifier)
            raise

        finally:
            if run_succeeded is False:
                self._set_successfully_created(value=False)
            elif run_succeeded is True:
                self._set_successfully_created(value=True)
            self.finalize_progress()


class EbayProductDeleteFactory(EbayProductBaseFactory):
    """Remove the offer and inventory item for a product."""

    def _delete_remote_records(self, *, remote_product: EbayProduct, child_remotes: list[EbayProduct]) -> None:
        to_delete = list(child_remotes)
        to_delete.append(remote_product)

        for target in to_delete:
            if target.pk is None:
                continue
            type(target).objects.filter(pk=target.pk).delete()

    def _collect_delete_errors(self, *, payload: Any) -> List[str]:
        if payload is None:
            return []

        if isinstance(payload, list):
            messages: List[str] = []
            for item in payload:
                messages.extend(self._collect_delete_errors(payload=item))
            return messages

        if isinstance(payload, dict):
            messages = self._extract_delete_errors_from_dict(payload=payload)
            for value in payload.values():
                messages.extend(self._collect_delete_errors(payload=value))
            return messages

        return []

    def _extract_delete_errors_from_dict(self, *, payload: Dict[str, Any]) -> List[str]:
        messages: List[str] = []
        error_message = payload.get("error")
        if error_message:
            messages.append(
                self._format_delete_error_message(
                    payload=payload,
                    message=str(error_message),
                )
            )

        api_errors = payload.get("errors")
        if isinstance(api_errors, list):
            for error in api_errors:
                if isinstance(error, dict):
                    message = error.get("message")
                    if message:
                        messages.append(str(message))
                elif error:
                    messages.append(str(error))

        return messages

    def _format_delete_error_message(self, *, payload: Dict[str, Any], message: str) -> str:
        details: List[str] = []
        sku = payload.get("sku")
        if sku:
            details.append(f"sku={sku}")
        remote_product_id = payload.get("remote_product_id")
        if remote_product_id:
            details.append(f"remote_product_id={remote_product_id}")
        if details:
            return f"{message} ({', '.join(details)})"
        return message

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        self.set_api()
        self.set_type()
        log_identifier, fixing_identifier = self.get_identifiers()

        try:
            self._resolve_remote_product()
            self.set_remote_product_for_logging()
            self.precalculate_progress_step_increment(2)
            self.update_progress()

            child_remotes: list[EbayProduct] = []
            if self._is_configurable_product():
                child_remotes = self._collect_child_remote_products()
                offer_responses = self.delete_offers_for_remote_products(remote_products=child_remotes)
                inventory_responses = self.delete_inventory_for_remote_products(remote_products=child_remotes)
                withdraw_result = self.withdraw_group()
                group_delete = self.delete_inventory_group()

                result = {
                    "withdraw": withdraw_result,
                    "children": {
                        "offers": offer_responses,
                        "inventory": inventory_responses,
                    },
                    "group": group_delete,
                }

                if not self.get_value_only:
                    remote_product = getattr(self, "remote_product", None)
                    if remote_product and getattr(remote_product, "remote_id", None):
                        remote_product.remote_id = None
                        self._update_remote_product_fields(
                            remote_product=remote_product,
                            fields=("remote_id",),
                        )
            else:
                offer_response = self.delete_offer()
                inventory_response = self.delete_inventory()
                result = {"offer": offer_response, "inventory": inventory_response}

            remote_product = getattr(self, "remote_product", None)

            self.update_progress()
            self.final_process()
            self.log_action(self.action_log, result or {}, self.payload, log_identifier)

            delete_errors = self._collect_delete_errors(payload=result or {})
            if delete_errors:
                message = "Delete failed:\n" + "\n".join(delete_errors)
                logger.error(message)

            if remote_product is not None:
                self._delete_remote_records(
                    remote_product=remote_product,
                    child_remotes=child_remotes,
                )
                self.remote_instance = None
                self.remote_product = None

            return result

        except Exception as exc:
            self.log_error(exc, self.action_log, log_identifier, self.payload, fixing_identifier)
            raise

        finally:
            self.finalize_progress()


class EbayProductVariationAddFactory(EbayProductBaseFactory):
    """Add a new variation to an existing configurable parent."""

    def _resolve_parent_remote_product(self) -> EbayProduct:
        parent_remote = getattr(self, "remote_parent_product", None)
        if parent_remote is not None:
            self._ensure_offer_for_remote(remote_product=parent_remote)
            return parent_remote

        parent_local = getattr(self, "parent_local_instance", None)
        if parent_local is None:
            raise ValueError("Parent product instance required for variation add")

        parent_remote = EbayProduct.objects.filter(
            local_instance=parent_local,
            sales_channel=self.sales_channel,
            remote_parent_product__isnull=True,
        ).first()

        if parent_remote is None:
            sku = self._get_sku(product=parent_local)
            parent_remote = EbayProduct.objects.create(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=parent_local,
                remote_sku=sku,
                remote_id=sku,
                is_variation=False,
            )

        self.remote_parent_product = parent_remote
        self._ensure_offer_for_remote(remote_product=parent_remote)
        return parent_remote

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        self._build_listing_policies()
        parent_remote = self._resolve_parent_remote_product()
        self._resolve_remote_product()
        self.set_api()
        self.validate()

        inventory_result = self.send_inventory_payload()

        if self.get_value_only:
            extras = self._post_inventory_push()
            with self._use_remote_product(parent_remote):
                group_payload = self.send_inventory_payload()
                group_publish = self.publish_group()

            value_only: Dict[str, Any] = {
                "inventory": inventory_result,
                "offer": self.build_offer_payload(),
                "group": group_payload,
                "group_publish": group_publish,
            }
            value_only.update(extras)
            return value_only

        offer_data = self._run_offer_sequence()
        extras = self._post_inventory_push()

        with self._use_remote_product(parent_remote):
            group_result = self.send_inventory_payload()
            group_publish = self.publish_group()

        result: Dict[str, Any] = {"inventory": inventory_result, "group": group_result, "group_publish": group_publish}
        result.update(offer_data)
        result.update(extras)
        return result


EbayProductBaseFactory.add_variation_factory = EbayProductVariationAddFactory


class EbayProductSyncFactory(EbayProductBaseFactory):
    """Dispatch to create or update depending on offer state."""

    def __init__(self, *, enable_price_update: bool = False, **kwargs) -> None:
        super().__init__(enable_price_update=enable_price_update, **kwargs)

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        remote_product = self._resolve_remote_product()
        offer_record = self._get_offer_record()
        has_offer = bool(offer_record and offer_record.remote_id)

        factory_cls = EbayProductUpdateFactory if has_offer else EbayProductCreateFactory
        factory = factory_cls(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_instance=remote_product,
            view=self.view,
            api=self.api,
            get_value_only=self.get_value_only,
            enable_price_update=self._enable_price_update,
        )
        return factory.run()
