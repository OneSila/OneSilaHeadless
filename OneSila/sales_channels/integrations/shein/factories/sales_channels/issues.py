from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from sales_channels.integrations.shein.factories.products.document_state import (
    SheinProductDocumentStateFactory,
)
from sales_channels.integrations.shein.models import SheinSalesChannel


class FetchRemoteIssuesFactory:
    """Fetch latest review issues for a Shein remote product.

    Mirrors the Amazon integration behaviour: executes synchronously and persists issues.
    """

    def __init__(self, *, remote_product, sales_channel) -> None:
        self.remote_product = remote_product
        self.sales_channel = sales_channel

    def validate(self) -> None:
        resolved_channel = (
            self.sales_channel.get_real_instance()
            if hasattr(self.sales_channel, "get_real_instance")
            else self.sales_channel
        )
        if not isinstance(resolved_channel, SheinSalesChannel):
            raise ValidationError(_("Provided sales channel is not a Shein integration."))

        if getattr(self.remote_product, "sales_channel_id", None) != getattr(resolved_channel, "id", None):
            raise ValidationError(_("Remote product does not belong to the provided Shein sales channel."))

        self.sales_channel = resolved_channel

    def run(self) -> dict[str, Any]:
        self.validate()
        factory = SheinProductDocumentStateFactory(
            sales_channel=self.sales_channel,
            remote_product=self.remote_product,
        )
        return factory.run()
