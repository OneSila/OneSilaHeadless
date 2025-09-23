from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core import models
from polymorphic.models import PolymorphicModel
from core.helpers import get_languages
from integrations.models import Integration
from sales_channels.models.mixins import RemoteObjectMixin
from sales_channels.managers import SalesChannelViewAssignManager, SalesChannelViewManager

import logging

logger = logging.getLogger(__name__)


class SalesChannel(Integration, models.Model):
    """
    Polymorphic model representing a sales channel, such as a website or marketplace.
    """

    use_configurable_name = models.BooleanField(default=False, verbose_name=_('Always use Configurable name over child'))
    sync_contents = models.BooleanField(default=True, verbose_name=_('Sync Contents'))
    sync_ean_codes = models.BooleanField(default=True, verbose_name=_('Sync EAN Codes'))
    sync_prices = models.BooleanField(default=True, verbose_name=_('Sync Prices'))
    import_orders = models.BooleanField(default=True, verbose_name=_('Import Orders'))
    first_import_complete = models.BooleanField(default=False, help_text="Set to True once the first import has been completed.")
    is_importing = models.BooleanField(default=False, help_text=_("True while an import process is running."))
    mark_for_delete = models.BooleanField(default=False, help_text="Set to True when shop is scheduled for deletion (e.g. from shopify/shop_redact).")

    is_external_install = models.BooleanField(
        default=False,
        help_text="True if the installation was initiated from the Shopify App Store or other stores."
    )

    class Meta:
        verbose_name = 'Sales Channel'
        verbose_name_plural = 'Sales Channels'

    def save(self, *args, **kwargs):

        dirty_fields = self.get_dirty_fields().keys()
        if 'active' in dirty_fields and self.active and 'is_importing' not in dirty_fields:
            if self.is_importing:
                raise Exception(
                    _("Cannot set integration to active during an import. It will automatically be set to the previous status after the import is done.")
                )

        self.connect()
        super().save(*args, **kwargs)

    def is_single_currency(self):
        from .taxes import RemoteCurrency

        remote_currencies_cnt = RemoteCurrency.objects.filter(sales_channel=self).count()
        return remote_currencies_cnt == 1

    def connect(self):
        raise NotImplementedError("The SalesChannel connect method must be implemented by child class")

    def __str__(self):
        return f"{self.hostname } @ {self.multi_tenant_company}"


class SalesChannelIntegrationPricelist(models.Model):
    """
    Through model to handle the association between a SalesChannel and a PriceList.
    """

    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    price_list = models.ForeignKey('sales_prices.SalesPriceList', on_delete=models.PROTECT)

    def clean(self):
        """Validate that price lists for a channel do not overlap per currency."""
        super().clean()

        currency = self.price_list.currency
        start = self.price_list.start_date
        end = self.price_list.end_date
        is_default = start is None and end is None

        existing = SalesChannelIntegrationPricelist.objects.filter(
            sales_channel=self.sales_channel,
            price_list__currency=currency,
        ).exclude(id=self.id)

        for integration in existing:
            other_start = integration.price_list.start_date
            other_end = integration.price_list.end_date
            other_is_default = other_start is None and other_end is None

            if is_default and other_is_default:
                raise ValidationError(
                    {
                        'price_list': _(
                            'Another fallback price list with the same currency already exists.'
                        )
                    }
                )

            if is_default or other_is_default:
                # Default price lists do not overlap with dated ones
                continue

            if None in [other_start, other_end, start, end] or (
                other_start <= end and start <= other_end
            ):
                raise ValidationError(
                    {
                        'price_list': _(
                            'Another price list with the same currency overlaps in date range.'
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

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

    name = models.CharField(max_length=216, null=True, blank=True)
    url = models.CharField(max_length=512, null=True, blank=True)

    objects = SalesChannelViewManager()

    class Meta:
        verbose_name = 'Sales Channel View'
        verbose_name_plural = 'Sales Channel Views'
        search_terms = ['name']

    def __str__(self):
        return str(self.name)


class SalesChannelViewAssign(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Model representing the assignment of a product to a specific sales channel view.
    """
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, db_index=True)
    sales_channel_view = models.ForeignKey('SalesChannelView', on_delete=models.CASCADE, db_index=True)
    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.SET_NULL, null=True,
                                       blank=True, help_text="The remote product associated with this assign.")
    needs_resync = models.BooleanField(default=False, help_text="Indicates if a resync is needed.")

    objects = SalesChannelViewAssignManager()

    class Meta:
        unique_together = ('product', 'sales_channel_view')
        verbose_name = 'Sales Channel View Assign'
        verbose_name_plural = 'Sales Channel View Assigns'
        ordering = ('product_id', 'sales_channel_view__name')
        search_terms = ['product__translations__name', 'product__sku', 'sales_channel_view__name']

    def __str__(self):
        return f"{self.product} @ {self.sales_channel_view}"

    @property
    def remote_url(self):
        """
        Returns the remote url for the product.
        """
        from sales_channels.integrations.shopify.models import ShopifySalesChannel
        from sales_channels.integrations.magento2.models import MagentoSalesChannel
        from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
        from sales_channels.integrations.amazon.models import (
            AmazonExternalProductId,
            AmazonSalesChannel,
            AmazonSalesChannelView,
        )

        sales_channel = self.sales_channel.get_real_instance()

        if isinstance(sales_channel, ShopifySalesChannel):
            return f"{self.sales_channel_view.url}/products/{self.product.url_key}"
        elif isinstance(sales_channel, MagentoSalesChannel):
            return f"{self.sales_channel_view.url}{self.product.url_key}.html"
        elif isinstance(sales_channel, WoocommerceSalesChannel):
            return f"{self.sales_channel_view.url}/products/{self.product.url_key}"
        elif isinstance(sales_channel, AmazonSalesChannel):
            try:
                asin = AmazonExternalProductId.objects.get(
                    product=self.product,
                    view=self.sales_channel_view,
                    type=AmazonExternalProductId.TYPE_ASIN,
                ).value
                return f"{self.sales_channel_view.url}/dp/{asin}"
            except AmazonExternalProductId.DoesNotExist:
                default_view = AmazonSalesChannelView.objects.filter(
                    sales_channel=sales_channel,
                    is_default=True,
                ).first()
                if default_view:
                    try:
                        asin = AmazonExternalProductId.objects.get(
                            product=self.product,
                            view=default_view,
                            type=AmazonExternalProductId.TYPE_ASIN,
                        ).value
                        return f"{self.sales_channel_view.url}/dp/{asin}"
                    except AmazonExternalProductId.DoesNotExist:
                        pass
            return None

        return f"{self.sales_channel_view.url}{self.product.url_key}.html"


class RemoteLanguage(PolymorphicModel, RemoteObjectMixin, models.Model):
    """
    Polymorphic model representing the remote mirror of a Language.
    This model tracks the synchronization status and data for remote languages.
    """
    LANGUAGE_CHOICES = get_languages()

    local_instance = models.CharField(
        max_length=7,
        choices=LANGUAGE_CHOICES,
        null=True,
        blank=True,
        help_text="The local language code associated with this remote language."
    )
    remote_code = models.CharField(max_length=64, help_text="The language code in the remote system.")

    class Meta:
        verbose_name = 'Remote Language'
        verbose_name_plural = 'Remote Languages'

    def __str__(self):
        return f"Remote language {self.local_instance} (Remote code: {self.remote_code}) on {self.sales_channel.hostname}"
