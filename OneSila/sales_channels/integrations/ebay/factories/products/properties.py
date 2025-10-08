from __future__ import annotations

from typing import Any

from sales_channels.factories.properties.properties import (
    RemoteProductPropertyCreateFactory,
    RemoteProductPropertyDeleteFactory,
    RemoteProductPropertyUpdateFactory,
)
from sales_channels.factories.mixins import PreFlightCheckError

from sales_channels.integrations.ebay.models.properties import (
    EbayProductProperty,
    EbayProperty,
    EbayPropertySelectValue,
)

from .mixins import EbayProductPropertyValueMixin


class EbayRemotePropertyEnsureFactory:
    """Stub factory raising when required eBay aspects are missing locally."""

    remote_model_class = EbayProperty

    def __init__(self, sales_channel, local_instance, api=None, **kwargs):
        self.sales_channel = sales_channel
        self.local_instance = local_instance
        self.api = api
        self.remote_instance = None

    def run(self):  # pragma: no cover - defensive path
        raise PreFlightCheckError(
            "eBay remote properties must be imported before syncing product attributes."
        )


class EbayRemotePropertySelectValueEnsureFactory:
    """Stub factory enforcing that aspect values are pre-imported."""

    remote_model_class = EbayPropertySelectValue

    def __init__(self, sales_channel, local_instance, api=None, **kwargs):
        self.sales_channel = sales_channel
        self.local_instance = local_instance
        self.api = api
        self.remote_instance = None

    def run(self):  # pragma: no cover - defensive path
        raise PreFlightCheckError(
            "eBay aspect values must be imported before syncing product attributes."
        )


class EbayProductPropertyCreateFactory(
    EbayProductPropertyValueMixin,
    RemoteProductPropertyCreateFactory,
):
    """Create remote product properties on eBay by resubmitting the inventory payload."""

    remote_model_class = EbayProductProperty
    remote_property_factory = EbayRemotePropertyEnsureFactory
    remote_property_select_value_factory = EbayRemotePropertySelectValueEnsureFactory

    def __init__(
        self,
        sales_channel,
        local_instance,
        remote_product,
        view,
        remote_property: EbayProperty,
        api=None,
        skip_checks: bool = False,
        get_value_only: bool = False,
        language=None,
    ):
        self.remote_property = remote_property
        super().__init__(
            sales_channel,
            local_instance,
            remote_product=remote_product,
            api=api,
            skip_checks=skip_checks,
            get_value_only=get_value_only,
            language=language,
            view=view,
        )

    def preflight_process(self):
        super().preflight_process()
        self.remote_value = self._compute_remote_value(remote_property=self.remote_property)

    def create_remote(self) -> Any:
        return self.send_inventory_payload()


class EbayProductPropertyUpdateFactory(
    EbayProductPropertyValueMixin,
    RemoteProductPropertyUpdateFactory,
):
    """Update eBay product properties using complete inventory item payloads."""

    remote_model_class = EbayProductProperty
    create_factory_class = EbayProductPropertyCreateFactory
    remote_property_factory = EbayRemotePropertyEnsureFactory
    remote_property_select_value_factory = EbayRemotePropertySelectValueEnsureFactory

    def __init__(
        self,
        sales_channel,
        local_instance,
        remote_product,
        view,
        api=None,
        get_value_only: bool = False,
        remote_instance=None,
        skip_checks: bool = False,
        language=None,
    ):
        super().__init__(
            sales_channel,
            local_instance,
            remote_product=remote_product,
            api=api,
            get_value_only=get_value_only,
            remote_instance=remote_instance,
            skip_checks=skip_checks,
            language=language,
            view=view,
        )

    def get_remote_value(self):
        remote_property = getattr(self.remote_instance, "remote_property", None)
        return self._compute_remote_value(remote_property=remote_property)

    def update_remote(self) -> Any:
        return self.send_inventory_payload()


class EbayProductPropertyDeleteFactory(
    EbayProductPropertyValueMixin,
    RemoteProductPropertyDeleteFactory,
):
    """Delete eBay product properties by re-sending the full inventory payload."""

    remote_model_class = EbayProductProperty
    remote_property_factory = EbayRemotePropertyEnsureFactory
    remote_property_select_value_factory = EbayRemotePropertySelectValueEnsureFactory

    def __init__(
        self,
        sales_channel,
        local_instance,
        remote_product,
        view,
        api=None,
        remote_instance=None,
    ):
        super().__init__(
            sales_channel,
            local_instance,
            remote_product=remote_product,
            api=api,
            remote_instance=remote_instance,
            view=view,
        )

    def delete_remote(self) -> Any:
        return self.send_inventory_payload()
