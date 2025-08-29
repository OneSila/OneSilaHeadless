from core.helpers import ensure_serializable
from sales_channels.integrations.amazon.factories.mixins import GetAmazonAPIMixin
from sales_channels.integrations.amazon.models import AmazonProductIssue


class FetchRecentlySyncedProductFactory(GetAmazonAPIMixin):
    """Fetch issues, ASIN, and image mappings for a remote product."""

    def __init__(self, *, remote_product, view, response_data=None, match_images=False):
        self.remote_product = remote_product
        self.view = view
        self.sales_channel = view.sales_channel.get_real_instance()
        self.response_data = response_data
        self.match_images = match_images

    def run(self):
        if not self._is_valid_product():
            return

        self._clear_existing_issues()
        response = self._get_response()
        issues, summaries, attributes = self._extract_sections(response)
        self._sync_asin(summaries)
        self._persist_issues(issues)
        if self.match_images:
            self._match_images(attributes)

    def _is_valid_product(self):
        return self.remote_product and getattr(self.remote_product, "remote_sku", None)

    def _clear_existing_issues(self):
        AmazonProductIssue.objects.filter(
            remote_product=self.remote_product,
            view=self.view,
            is_validation_issue=False,
        ).delete()

    def _get_response(self):
        if self.response_data:
            return self.response_data
        return self.get_listing_item(
            self.remote_product.remote_sku,
            self.view.remote_id,
            included_data=["issues", "summaries", "attributes"],
        )

    def _extract_sections(self, response):
        if isinstance(response, dict):
            issues_data = response.get("issues", []) or []
            summaries = response.get("summaries", []) or []
            attributes = response.get("attributes", {}) or {}
        else:
            issues_data = getattr(response, "issues", []) or []
            summaries = getattr(response, "summaries", []) or []
            attributes = getattr(response, "attributes", {}) or {}
        return issues_data, summaries, attributes

    def _sync_asin(self, summaries):
        if not summaries:
            return
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

    def _persist_issues(self, issues_data):
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

    def _match_images(self, attributes):
        if not self.remote_product.product_owner or not getattr(self.remote_product, "local_instance", None):
            return

        from media.models import Media, MediaProductThrough
        from sales_channels.integrations.amazon.models import AmazonImageProductAssociation
        from sales_channels.integrations.amazon.image_similarity import phash_is_same

        image_keys = [
            "main_product_image_locator",
            *[f"other_product_image_locator_{i}" for i in range(1, 9)],
        ]
        remote_urls = []
        for key in image_keys:
            val = attributes.get(key) if isinstance(attributes, dict) else getattr(attributes, key, None)
            if not val:
                continue
            item = val[0] if isinstance(val, list) else val
            url = item.get("media_location") if isinstance(item, dict) else getattr(item, "media_location", None)
            if url:
                remote_urls.append(url)

        if not remote_urls:
            return

        throughs = (
            MediaProductThrough.objects.filter(
                product=self.remote_product.local_instance, media__type=Media.IMAGE
            ).order_by("sort_order")
        )

        for through, remote_url in zip(throughs, remote_urls):
            local_path = getattr(through.media.image, "path", None)
            if not local_path:
                continue
            try:
                is_same = phash_is_same(local_path, remote_url, threshold=95.0)
            except Exception:
                continue
            if not is_same:
                continue
            instance, _ = AmazonImageProductAssociation.objects.get_or_create(
                multi_tenant_company=self.view.multi_tenant_company,
                sales_channel=self.sales_channel,
                local_instance=through,
                remote_product=self.remote_product,
            )
            if instance.imported_url != remote_url:
                instance.imported_url = remote_url
                instance.save(update_fields=["imported_url"])
