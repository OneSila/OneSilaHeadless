from __future__ import annotations

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
from sales_channels.integrations.ebay.factories.products.properties import (
    EbayProductPropertyCreateFactory,
    EbayProductPropertyDeleteFactory,
    EbayProductPropertyUpdateFactory,
)
from sales_channels.integrations.ebay.factories.prices import EbayPriceUpdateFactory
from sales_channels.integrations.ebay.models.products import EbayProduct
from sales_channels.integrations.ebay.models.properties import (
    EbayProductProperty,
    EbayProperty,
)
from sales_channels.models.sales_channels import SalesChannelViewAssign


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
        **kwargs: Any,
    ) -> None:
        self.view = view
        self.get_value_only = get_value_only
        self._enable_price_update = True
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

    # ------------------------------------------------------------------
    # Base utilities
    # ------------------------------------------------------------------
    def preflight_check(self) -> bool:
        return self.view is not None and super().preflight_check()

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

            self._ensure_assign(remote_product=remote_child)
            remote_children.append(remote_child)

        return remote_children

    def _run_configurable_sequence(self) -> Dict[str, Any]:
        self._build_listing_policies()
        child_remotes = self._collect_child_remote_products()

        children_payloads = {
            "inventory": self.send_bulk_inventory_payloads(remote_products=child_remotes),
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
        self._ensure_assign(remote_product=remote_product)
        return remote_product

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
            for product_property in product_properties:
                remote_property = EbayProperty.objects.filter(
                    sales_channel=self.sales_channel,
                    marketplace=self.view,
                    local_instance=product_property.property,
                ).first()
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._enable_price_update = False

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        self.set_api()
        self.set_type()
        log_identifier, fixing_identifier = self.get_identifiers()

        try:
            self._build_listing_policies()
            self._resolve_remote_product()
            self.set_remote_product_for_logging()
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
            return result

        except Exception as exc:
            self.log_error(exc, self.action_log, log_identifier, self.payload, fixing_identifier)
            raise

        finally:
            self.finalize_progress()


class EbayProductUpdateFactory(EbayProductBaseFactory):
    """Refresh inventory and offer data for an existing listing."""

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        self.set_api()
        self.set_type()
        log_identifier, fixing_identifier = self.get_identifiers()

        try:
            self._build_listing_policies()
            self._resolve_remote_product()
            self.set_remote_product_for_logging()
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
            return result

        except Exception as exc:
            self.log_error(exc, self.action_log, log_identifier, self.payload, fixing_identifier)
            raise

        finally:
            self.finalize_progress()


class EbayProductDeleteFactory(EbayProductBaseFactory):
    """Remove the offer and inventory item for a product."""

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

            if self._is_configurable_product():
                child_remotes = self._collect_child_remote_products()
                withdraw_result = self.withdraw_group()
                offer_responses = self.delete_offers_for_remote_products(remote_products=child_remotes)
                group_delete = self.delete_inventory_group()
                inventory_responses = self.delete_inventory_for_remote_products(remote_products=child_remotes)

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

            self.update_progress()
            self.final_process()
            self.log_action(self.action_log, result or {}, self.payload, log_identifier)
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
            self._ensure_assign(remote_product=parent_remote)
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
        self._ensure_assign(remote_product=parent_remote)
        return parent_remote

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        self._build_listing_policies()
        parent_remote = self._resolve_parent_remote_product()
        self._resolve_remote_product()
        self.set_api()

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

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        remote_product = self._resolve_remote_product()
        assign = self._ensure_assign()
        has_offer = bool(assign and assign.remote_id)

        factory_cls = EbayProductUpdateFactory if has_offer else EbayProductCreateFactory
        factory = factory_cls(
            sales_channel=self.sales_channel,
            local_instance=self.local_instance,
            remote_instance=remote_product,
            view=self.view,
            api=self.api,
            get_value_only=self.get_value_only,
        )
        return factory.run()
