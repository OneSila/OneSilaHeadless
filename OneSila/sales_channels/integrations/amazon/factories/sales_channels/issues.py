from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.models import SalesChannelViewAssign


class RefreshLatestIssuesFactory(GetAmazonAPIMixin):
    """Fetch latest listing issues for a single marketplace assignment."""

    def __init__(self, assign: SalesChannelViewAssign):
        self.assign = assign
        self.sales_channel = assign.sales_channel
        self.view = assign.sales_channel_view

    def run(self):
        remote_product = self.assign.remote_product
        if not remote_product or not remote_product.remote_sku:
            return

        response = self.get_listing_item(
            remote_product.remote_sku,
            self.view.remote_id,
            included_data=["issues", "updates"],
        )
        issues = getattr(response, "issues", []) or []
        self.assign.issues = [
            issue.to_dict() if hasattr(issue, "to_dict") else issue
            for issue in issues
        ]
        self.assign.save()
