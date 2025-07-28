from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.models import SalesChannelViewAssign
from core.helpers import ensure_serializable


class RefreshLatestIssuesFactory(GetAmazonAPIMixin):
    """Fetch latest listing issues for a single marketplace assignment."""

    def __init__(self, assign: SalesChannelViewAssign):
        self.assign = assign
        self.sales_channel = assign.sales_channel.get_real_instance()
        self.view = assign.sales_channel_view

    def run(self):
        remote_product = self.assign.remote_product
        if not remote_product or not remote_product.remote_sku:
            return

        response = self.get_listing_item(
            remote_product.remote_sku,
            self.view.remote_id,
            included_data=["issues"],
        )
        issues = getattr(response, "issues", []) or []
        self.assign.issues = [
            ensure_serializable(
                issue.to_dict() if hasattr(issue, "to_dict") else issue
            )
            for issue in issues
        ]
        self.assign.save()
