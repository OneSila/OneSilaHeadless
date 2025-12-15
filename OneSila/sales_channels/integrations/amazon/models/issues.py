from core import models


class AmazonProductIssue(models.Model):
    """Store issues reported for Amazon remote products per marketplace."""

    remote_product = models.ForeignKey(
        'amazon.AmazonProduct',
        on_delete=models.CASCADE,
        related_name='issues',
        help_text='The Amazon remote product this issue refers to.',
    )
    view = models.ForeignKey(
        'amazon.AmazonSalesChannelView',
        on_delete=models.CASCADE,
        related_name='product_issues',
        help_text='The Amazon marketplace where the issue was found.',
    )
    code = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=255, null=True, blank=True)
    categories = models.JSONField(default=list, blank=True)
    enforcement_actions = models.JSONField(default=list, blank=True)
    enforcement_exemption_status = models.CharField(max_length=32, null=True, blank=True)
    enforcement_exemption_expiry_date = models.DateTimeField(null=True, blank=True)
    enforcement_attribute_names = models.JSONField(default=list, blank=True)
    is_suppressed = models.BooleanField(default=False, db_index=True)
    is_validation_issue = models.BooleanField(default=False)
    raw_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = 'Amazon Product Issue'
        verbose_name_plural = 'Amazon Product Issues'
        ordering = ('remote_product_id', 'view_id')

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.remote_product_id}:{self.code}"
