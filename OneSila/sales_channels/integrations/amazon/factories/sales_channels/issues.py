from core.helpers import ensure_serializable
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import AmazonProduct, AmazonProductIssue
from sales_channels.integrations.amazon.tasks import resync_amazon_product_db_task


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
                included_data=["issues", "summaries"],
            )

        if isinstance(response, dict):
            issues_data = response.get("issues", []) or []
            summaries = response.get("summaries", []) or []
        else:
            issues_data = getattr(response, "issues", []) or []
            summaries = getattr(response, "summaries", []) or []

        asin = None
        if summaries:
            summary = summaries[0]
            asin = summary.get("asin") if isinstance(summary, dict) else getattr(summary, "asin", None)
            if asin and getattr(self.remote_product, "local_instance", None):
                from sales_channels.integrations.amazon.models import AmazonExternalProductId

                product = self.remote_product.local_instance
                try:
                    ext = AmazonExternalProductId.objects.get(product=product, view=self.view)
                    if ext.created_asin != asin:
                        ext.created_asin = asin
                        ext.save(update_fields=["created_asin"])
                except AmazonExternalProductId.DoesNotExist:
                    AmazonExternalProductId.objects.create(
                        multi_tenant_company=self.remote_product.multi_tenant_company,
                        product=product,
                        view=self.view,
                        type=AmazonExternalProductId.TYPE_ASIN,
                        value=asin,
                        created_asin=asin,
                    )

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

        override_status = self.remote_product.STATUS_APPROVAL_REJECTED if (not asin and issues_data) else None
        self.remote_product.refresh_status(commit=True, override_status=override_status)

        self._auto_fix_partially_listed()

        child_products = (
            AmazonProduct.objects.filter(remote_parent_product=self.remote_product)
            .select_related("local_instance", "sales_channel")
        )

        for child_product in child_products.iterator():
            FetchRemoteIssuesFactory(remote_product=child_product, view=self.view).run()

    def _auto_fix_partially_listed(self) -> None:
        if self.remote_product.status != self.remote_product.STATUS_PARTIALLY_LISTED:
            return

        if not getattr(self.remote_product, "local_instance_id", None):
            return

        from sales_channels.integrations.amazon.models import AmazonSalesChannelView
        from sales_channels.models.sales_channels import SalesChannelViewAssign

        created_marketplaces = set(self.remote_product.created_marketplaces or [])
        missing_view_ids = list(
            SalesChannelViewAssign.objects.filter(remote_product=self.remote_product)
            .exclude(sales_channel_view__remote_id__in=created_marketplaces)
            .values_list("sales_channel_view_id", flat=True)
            .distinct()
        )
        if not missing_view_ids:
            return

        count = 1 + (getattr(self.remote_product.local_instance, "get_configurable_variations", lambda: [])().count())
        for view in AmazonSalesChannelView.objects.filter(id__in=missing_view_ids).select_related("sales_channel"):
            from sales_channels.integrations.amazon.factories.task_queue import AmazonSingleViewAddTask

            task_runner = AmazonSingleViewAddTask(
                task_func=resync_amazon_product_db_task,
                view=view,
                number_of_remote_requests=count,
            )
            task_runner.set_extra_task_kwargs(
                product_id=self.remote_product.local_instance_id,
                remote_product_id=self.remote_product.id,
                force_validation_only=False,
                force_full_update=True,
            )
            task_runner.run()


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
