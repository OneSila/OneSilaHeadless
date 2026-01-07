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
    starting_stock = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Initial stock quantity to send when creating remote products.",
    )
    min_name_length = models.PositiveIntegerField(
        default=150,
        help_text=_("Minimum product name length enforced by this sales channel."),
    )
    min_description_length = models.PositiveIntegerField(
        default=1000,
        help_text=_("Minimum product description length enforced by this sales channel."),
    )

    gpt_enable = models.BooleanField(default=False, help_text=_("Enable GPT-generated product feed configuration."))
    gpt_enable_checkout = models.BooleanField(default=False, help_text=_("Allow GPT-generated content to power checkout experiences."))
    gpt_seller_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Display name presented in GPT-powered experiences."),
    )
    gpt_seller_url = models.URLField(
        null=True,
        blank=True,
        help_text=_("Uses the hostname by default; override here to present a different seller URL."),
    )
    gpt_seller_privacy_policy = models.URLField(
        null=True,
        blank=True,
        help_text=_("Link to your privacy policy when GPT checkout is enabled."),
    )
    gpt_seller_tos = models.URLField(
        null=True,
        blank=True,
        help_text=_("Link to your terms of service when GPT checkout is enabled."),
    )
    gpt_return_policy = models.URLField(
        null=True,
        blank=True,
        help_text=_("Public return policy URL required when GPT is enabled."),
    )
    gpt_return_window = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Return window (for example, in days) required when GPT is enabled."),
    )
    is_external_install = models.BooleanField(
        default=False,
        help_text="True if the installation was initiated from the Shopify App Store or other stores."
    )

    class Meta:
        verbose_name = 'Sales Channel'
        verbose_name_plural = 'Sales Channels'

    def clean(self):
        super().clean()

        errors = {}

        if self.gpt_enable:
            required_on_enable = {
                "gpt_seller_name": _("Seller name is required when GPT is enabled."),
                "gpt_return_policy": _("Return policy URL is required when GPT is enabled."),
                "gpt_return_window": _("Return window is required when GPT is enabled."),
            }
            for field, message in required_on_enable.items():
                value = getattr(self, field)
                if value in (None, ""):
                    errors[field] = ValidationError(message)

        if self.gpt_enable_checkout:
            if not self.gpt_enable:
                errors["gpt_enable_checkout"] = ValidationError(_("Enable GPT before enabling GPT checkout."))
            checkout_required = {
                "gpt_seller_privacy_policy": _("Privacy policy URL is required when GPT checkout is enabled."),
                "gpt_seller_tos": _("Terms of service URL is required when GPT checkout is enabled."),
            }
            for field, message in checkout_required.items():
                value = getattr(self, field)
                if value in (None, ""):
                    errors[field] = ValidationError(message)

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):

        dirty_fields = self.get_dirty_fields().keys()
        if 'active' in dirty_fields and self.active and 'is_importing' not in dirty_fields:
            if self.is_importing:
                raise Exception(
                    _("Please wait until the import has fully completed.  Then mark the integration as active.")
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

    def ensure_gpt_feed(self):
        from .gpt import SalesChannelGptFeed

        feed, _ = SalesChannelGptFeed.objects.get_or_create(
            sales_channel=self,
            multi_tenant_company=self.multi_tenant_company,
        )
        return feed

    @property
    def gpt_feed(self):
        from .gpt import SalesChannelGptFeed

        try:
            return self.gpt_feed_record
        except SalesChannelGptFeed.DoesNotExist:
            return None


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
    STATUS_CREATED = "CREATED"
    STATUS_PENDING_CREATION = "PENDING_CREATION"
    STATUS_CHOICES = (
        (STATUS_CREATED, _("Created")),
        (STATUS_PENDING_CREATION, _("Pending creation")),
    )

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, db_index=True)
    sales_channel_view = models.ForeignKey('SalesChannelView', on_delete=models.CASCADE, db_index=True)
    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.SET_NULL, null=True,
                                       blank=True, help_text="The remote product associated with this assign.")
    link = models.URLField(
        max_length=2048,
        null=True,
        blank=True,
        help_text="Remote product URL for this view assignment.",
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        blank=True,
        null=True,
        help_text=_("Local assignment status for the view assignment."),
    )
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

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        previous_status = self.status
        is_new = self.pk is None
        self._set_pending_creation_status(is_new=is_new)

        if update_fields is not None and previous_status != self.status:
            update_fields = set(update_fields)
            update_fields.add("status")
            kwargs["update_fields"] = list(update_fields)

        return super().save(*args, **kwargs)

    def _set_pending_creation_status(self, *, is_new: bool) -> None:
        if not is_new or self.remote_product_id:
            return

        view = getattr(self, "sales_channel_view", None)
        if view is None:
            return

        resolved_view = view.get_real_instance() if hasattr(view, "get_real_instance") else view
        if resolved_view is None:
            return

        from sales_channels.integrations.shein.models import SheinSalesChannelView

        if isinstance(resolved_view, SheinSalesChannelView):
            self.status = self.STATUS_PENDING_CREATION

    @property
    def remote_url(self):
        """
        Returns the remote url for the product.
        """
        from sales_channels.integrations.shopify.models import ShopifySalesChannel
        from sales_channels.integrations.magento2.models import MagentoSalesChannel
        from sales_channels.integrations.woocommerce.models import WoocommerceSalesChannel
        from sales_channels.integrations.shein.models import SheinSalesChannel
        from sales_channels.integrations.amazon.models import (
            AmazonExternalProductId,
            AmazonSalesChannel,
            AmazonSalesChannelView,
        )
        from sales_channels.integrations.ebay.models import (
            EbaySalesChannel,
        )

        sales_channel = self.sales_channel.get_real_instance()

        if isinstance(sales_channel, ShopifySalesChannel):
            return f"{self.sales_channel_view.url}/products/{self.product.url_key}"
        elif isinstance(sales_channel, MagentoSalesChannel):
            return f"{self.sales_channel_view.url}{self.product.url_key}.html"
        elif isinstance(sales_channel, WoocommerceSalesChannel):
            return f"{self.sales_channel_view.url}/products/{self.product.url_key}"
        elif isinstance(sales_channel, SheinSalesChannel):
            return self.link or None
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
        elif isinstance(sales_channel, EbaySalesChannel):
            listing_id = None

            if self.remote_product and self.remote_product.id:
                from sales_channels.integrations.ebay.models.products import EbayProductOffer

                offer = (
                    EbayProductOffer.objects.filter(
                        remote_product_id= self.remote_product.id,
                        sales_channel_view=self.sales_channel_view,
                    )
                    .only("remote_id", "listing_id")
                    .first()
                )

                if offer:
                    listing_id = (offer.listing_id or "").strip()
                    listing_status = (offer.listing_status or "").strip()

            base_url = (self.sales_channel_view.url or "").rstrip('/') if self.sales_channel_view else ""

            if sales_channel.environment == EbaySalesChannel.SANDBOX:
                base_url = "https://sandbox.ebay.com"
            elif not base_url:
                base_url = "https://www.ebay.com"

            if listing_id:
                return f"{base_url.rstrip('/')}/itm/{listing_id}"

            return None

        return None


class SalesChannelContentTemplate(models.Model):
    """Custom HTML template per sales channel and language."""

    sales_channel = models.ForeignKey(
        'SalesChannel',
        on_delete=models.CASCADE,
        related_name='content_templates',
    )

    language = models.CharField(
        max_length=7,
        choices=get_languages(),
        help_text="Language code this template targets.",
    )
    template = models.TextField(help_text="Django template used to render product descriptions.")
    add_as_iframe = models.BooleanField(
        default=False,
        help_text="Render the template output inside an iframe when syncing content.",
    )

    class Meta:
        verbose_name = 'Sales Channel Content Template'
        verbose_name_plural = 'Sales Channel Content Templates'
        constraints = [
            models.UniqueConstraint(
                fields=['sales_channel', 'language'],
                name='unique_sales_channel_language_template',
            ),
        ]

    def __str__(self):
        return f"{self.sales_channel} ({self.language})"


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
