from core.helpers import ensure_serializable
from sales_channels.integrations.amazon.models import AmazonProductIssue


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
