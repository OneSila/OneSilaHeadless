from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core import models
from polymorphic.models import PolymorphicModel
from django.conf import settings
from core.helpers import get_languages
from core.huey import DEFAULT_PRIORITY
from integrations.models import Integration
from sales_channels.models.mixins import RemoteObjectMixin
from django.utils.timezone import now

import logging

logger = logging.getLogger(__name__)

class SalesChannel(Integration, models.Model):
    """
    Polymorphic model representing a sales channel, such as a website or marketplace.
    """

    use_configurable_name = models.BooleanField(default=False,verbose_name=_('Always use Configurable name over child'))
    sync_contents = models.BooleanField(default=True, verbose_name=_('Sync Contents'))
    sync_orders_after = models.DateTimeField(null=True, blank=True, verbose_name=_('Sync Orders After Date'))

    class Meta:
        verbose_name = 'Sales Channel'
        verbose_name_plural = 'Sales Channels'

    def __str__(self):
        return f"{self.hostname } @ {self.multi_tenant_company}"

class SalesChannelIntegrationPricelist(models.Model):
    """
    Through model to handle the association between a SalesChannel and a PriceList.
    """

    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    price_list = models.ForeignKey('sales_prices.SalesPriceList', on_delete=models.PROTECT)
    # @TODO: Add save override validation

    class Meta:
        unique_together = ('sales_channel', 'price_list')
        verbose_name = 'Sales Channel Integration Pricelist'
        verbose_name_plural = 'Sales Channel Integration Pricelists'

    def __str__(self):
        return f"{self.sales_channel} - {self.price_list}"

class SalesChannelView(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Model representing a specific view of a sales channel
    """

    name = models.CharField(max_length=100)
    url = models.CharField(max_length=512, null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('sales_channel', 'name')
        verbose_name = 'Sales Channel View'
        verbose_name_plural = 'Sales Channel Views'

    def __str__(self):
        return self.name

class SalesChannelViewAssign(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Model representing the assignment of a product to a specific sales channel view.
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, db_index=True)
    sales_channel_view = models.ForeignKey('SalesChannelView', on_delete=models.CASCADE, db_index=True)
    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.SET_NULL, null=True, blank=True, help_text="The remote product associated with this assign.")
    needs_resync = models.BooleanField(default=False, help_text="Indicates if a resync is needed.")

    class Meta:
        unique_together = ('product', 'sales_channel_view')
        verbose_name = 'Sales Channel View Assign'
        verbose_name_plural = 'Sales Channel View Assigns'
        ordering = ('product_id', 'sales_channel_view__name')

    def __str__(self):
        return f"{self.product} @ {self.sales_channel_view}"

    @property
    def remote_url(self):
        return f"{self.sales_channel_view.url}{self.product.url_key}.html"

    def create_clean(self):
        # Prevent assignment if the product is not for sale
        if not self.product.for_sale:
            raise ValidationError(f"Cannot assign product '{self.product}' to sales channel view because it is not marked for sale.")

        if self.product.inspector.has_missing_information:
            raise ValidationError(f"Cannot assign product '{self.product}' to sales channel view because it is having missing informations..")

    def save(self, *args, **kwargs):
        if not self.pk:
            self.create_clean()
        super().save(*args, **kwargs)

class RemoteLanguage(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a Language.
    This model tracks the synchronization status and data for remote languages.
    """
    LANGUAGE_CHOICES = get_languages()

    local_instance = models.CharField(
        max_length=7,
        choices=LANGUAGE_CHOICES,
        default=settings.LANGUAGE_CODE,
        help_text="The local language code associated with this remote language."
    )
    remote_code = models.CharField(max_length=10, help_text="The language code in the remote system.")

    class Meta:
        unique_together = ('sales_channel', 'local_instance')
        verbose_name = 'Remote Language'
        verbose_name_plural = 'Remote Languages'

    def __str__(self):
        return f"Remote language {self.local_instance} (Remote code: {self.remote_code}) on {self.sales_channel.hostname}"