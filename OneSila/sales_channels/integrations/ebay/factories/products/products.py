from __future__ import annotations

from typing import Any, Dict, Optional

from sales_channels.factories.products.products import RemoteProductSyncFactory
from properties.models import ProductProperty

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

    def _resolve_remote_product(self) -> EbayProduct:
        remote_product = getattr(self, "remote_instance", None)
        if remote_product is None:
            remote_product = EbayProduct.objects.filter(
                local_instance=self.local_instance,
                sales_channel=self.sales_channel,
                remote_parent_product__isnull=True,
            ).first()

        created = False
        if remote_product is None:
            remote_product = EbayProduct.objects.create(
                multi_tenant_company=self.sales_channel.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=self.local_instance,
                remote_sku=self.local_instance.sku,
                is_variation=False,
            )
            created = True

        updates: list[str] = []
        sku = self._get_sku(product=self.local_instance)

        if remote_product.remote_sku != sku:
            remote_product.remote_sku = sku
            updates.append("remote_sku")

        if created or not remote_product.remote_id:
            remote_product.remote_id = sku
            if "remote_id" not in updates:
                updates.append("remote_id")

        if updates:
            remote_product.save(update_fields=updates)

        self.remote_product = remote_product
        self.remote_instance = remote_product
        self._ensure_assign()
        return remote_product

    def _ensure_assign(self) -> Optional[SalesChannelViewAssign]:
        assign = super()._ensure_assign()
        if assign and assign.remote_product_id != getattr(self.remote_product, "id", None):
            assign.remote_product = self.remote_product
            assign.save(update_fields=["remote_product"])
        return assign

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
            return {"listing_description": self.get_listing_description()}

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

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        self._resolve_remote_product()
        self.set_api()
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

        result: Dict[str, Any] = {"inventory": inventory_result}
        result.update(offer_data)
        result.update(extras)
        return result


class EbayProductUpdateFactory(EbayProductBaseFactory):
    """Refresh inventory and offer data for an existing listing."""

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        self._resolve_remote_product()
        self.set_api()
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

        result: Dict[str, Any] = {"inventory": inventory_result}
        result.update(offer_data)
        result.update(extras)
        return result


class EbayProductDeleteFactory(EbayProductBaseFactory):
    """Remove the offer and inventory item for a product."""

    def run(self) -> Optional[Dict[str, Any]]:
        if not self.preflight_check():
            return None

        self._resolve_remote_product()
        self.set_api()

        offer_response = self.delete_offer()
        inventory_response = self.delete_inventory()

        return {
            "offer": offer_response,
            "inventory": inventory_response,
        }


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
