from core import models
from integrations.models import IntegrationObjectMixin

class RemoteObjectMixin(IntegrationObjectMixin):
    """
    Mixin for objects that are tied to a specific sales_channel integration.
    """
    sales_channel = models.ForeignKey('sales_channels.SalesChannel', on_delete=models.CASCADE, db_index=True)

    @property
    def integration(self):
        """
        Returns the sales_channel as the integration.
        """
        return self.sales_channel

    class Meta:
        abstract = True
