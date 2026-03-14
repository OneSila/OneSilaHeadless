from sales_channels.factories.mixins import PullRemoteInstanceMixin
from sales_channels.integrations.mirakl.factories.mixins import GetMiraklAPIMixin
from sales_channels.integrations.mirakl.models import MiraklSalesChannelView


class MiraklSalesChannelViewPullFactory(GetMiraklAPIMixin, PullRemoteInstanceMixin):
    """Pull Mirakl channels as sales channel views."""

    remote_model_class = MiraklSalesChannelView
    field_mapping = {
        "remote_id": "code",
        "name": "label",
        "description": "description",
    }
    update_field_mapping = field_mapping
    get_or_create_fields = ["remote_id"]

    allow_create = True
    allow_update = True
    allow_delete = False
    is_model_response = False

    def fetch_remote_instances(self):
        response = self.mirakl_get(path="/api/channels")
        channels = response.get("channels") or []
        self.remote_instances = [channel for channel in channels if isinstance(channel, dict)]
