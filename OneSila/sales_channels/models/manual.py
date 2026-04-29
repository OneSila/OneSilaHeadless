from sales_channels.models.sales_channels import SalesChannel, SalesChannelView


class ManualSalesChannel(SalesChannel):
    class Meta:
        verbose_name = "Manual Sales Channel"
        verbose_name_plural = "Manual Sales Channels"

    def connect(self) -> bool:
        return True

    def __str__(self) -> str:
        return f"Manual Sales Channel: {self.hostname}"


class ManualSalesChannelView(SalesChannelView):
    class Meta:
        verbose_name = "Manual Sales Channel View"
        verbose_name_plural = "Manual Sales Channel Views"

    def __str__(self) -> str:
        return self.name or super().__str__()
