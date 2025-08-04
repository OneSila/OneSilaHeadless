from core.helpers import ensure_serializable
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import AmazonProductIssue


class FetchRemoteIssuesFactory(GetAmazonAPIMixin):
    """Fetch latest listing issues for a remote product in a marketplace."""

    def __init__(self, *, remote_product, view, response_data=None):
        self.remote_product = remote_product
        self.view = view
        self.sales_channel = view.sales_channel.get_real_instance()
        self.response_data = response_data

    def run(self):

        if not self.remote_product or not getattr(self.remote_product, 'remote_sku', None):
            return

        AmazonProductIssue.objects.filter(
            remote_product=self.remote_product,
            view=self.view,
            is_validation_issue=False,
        ).delete()

        if self.response_data:
            response = self.response_data
        else:
            response = self.get_listing_item(
                self.remote_product.remote_sku,
                self.view.remote_id,
                included_data=["issues"],
            )

        if isinstance(response, dict):
            issues_data = response.get("issues", []) or []
        else:
            issues_data = getattr(response, "issues", []) or []

        for issue in issues_data:
            data = ensure_serializable(
                issue.to_dict() if hasattr(issue, "to_dict") else issue
            )
            AmazonProductIssue.objects.create(
                multi_tenant_company=self.view.multi_tenant_company,
                remote_product=self.remote_product,
                view=self.view,
                code=data.get("code"),
                message=data.get("message"),
                severity=data.get("severity"),
                raw_data=data,
                is_validation_issue=False,
            )


class FetchRemoteValidationIssueFactory:
    """Persist validation issues returned from API submissions."""

    def __init__(self, *, remote_product, view, issues):
        self.remote_product = remote_product
        self.view = view
        self.issues = issues or []

    def run(self):
        if not self.remote_product:
            return

        AmazonProductIssue.objects.filter(
            remote_product=self.remote_product,
            view=self.view,
            is_validation_issue=True,
        ).delete()

        for issue in self.issues:
            data = ensure_serializable(
                issue.to_dict() if hasattr(issue, "to_dict") else issue
            )

            AmazonProductIssue.objects.create(
                multi_tenant_company=self.view.multi_tenant_company,
                remote_product=self.remote_product,
                view=self.view,
                code=data.get("code"),
                message=data.get("message"),
                severity=data.get("severity"),
                raw_data=data,
                is_validation_issue=True,
            )
