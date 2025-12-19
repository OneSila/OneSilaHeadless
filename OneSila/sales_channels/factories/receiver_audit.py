import logging


logger = logging.getLogger(__name__)


class RemoteReceiverAuditFactory:
    """
    No-op factory used by receiver audit tasks.

    It exists to keep the task queue + logging consistent with real tasks, while ensuring
    no remote calls or mutations are performed.
    """

    def __init__(
        self,
        *,
        integration_label: str,
        event_name: str,
        sales_channel,
        view=None,
        remote_product=None,
        context: dict | None = None,
    ):
        self.integration_label = integration_label
        self.event_name = event_name
        self.sales_channel = sales_channel
        self.view = view
        self.remote_product = remote_product
        self.context = {k: v for k, v in (context or {}).items() if v is not None}

        local_product = getattr(remote_product, "local_instance", None) if remote_product is not None else None

        logger.info(
            "%s receiver audit queued: event=%s sales_channel_id=%s view_id=%s remote_product_id=%s local_product_id=%s context=%s",
            integration_label,
            event_name,
            getattr(sales_channel, "id", None),
            getattr(view, "id", None),
            getattr(remote_product, "id", None),
            getattr(local_product, "id", None),
            self.context,
        )

    def run(self) -> None:
        return

