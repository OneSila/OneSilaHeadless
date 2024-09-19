from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core import models
from polymorphic.models import PolymorphicModel
from django.conf import settings
from core.helpers import get_languages
from core.huey import DEFAULT_PRIORITY
from sales_channels.models.mixins import RemoteObjectMixin
from django.utils.timezone import now

import logging

logger = logging.getLogger(__name__)

class SalesChannel(PolymorphicModel, models.Model):
    """
    Polymorphic model representing a sales channel, such as a website or marketplace.
    """

    hostname = models.URLField()
    active = models.BooleanField(default=True)
    verify_ssl = models.BooleanField(default=True)
    requests_per_minute = models.IntegerField(default=60)
    use_configurable_name = models.BooleanField(default=False,verbose_name=_('Always use Configurable name over child'))
    sync_contents = models.BooleanField(default=False, verbose_name=_('Sync Contents'))
    sync_orders_after = models.DateTimeField(null=True, blank=True, verbose_name=_('Sync Orders After Date'))

    class Meta:
        unique_together = ('multi_tenant_company', 'hostname')
        verbose_name = 'Sales Channel'
        verbose_name_plural = 'Sales Channels'

    def __str__(self):
        return self.hostname

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

class RemoteTaskQueue(models.Model):
    PENDING = 'PENDING'
    PROCESSING = 'PROCESSING'
    PROCESSED = 'PROCESSED'
    FAILED = 'FAILED'  # New status
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (PROCESSED, 'Processed'),
        (FAILED, 'Failed'),  # New status choice
    ]

    sales_channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255)
    task_args = models.JSONField(null=True, blank=True)
    task_kwargs = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    sent_to_queue_at = models.DateTimeField(default=now)
    retry = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)
    number_of_remote_requests = models.IntegerField(default=1) # how many remote requests does this task do?
    priority = models.IntegerField(default=DEFAULT_PRIORITY)

    @property
    def name(self):
        """Extracts the simplified task name from the task path."""
        return self.task_name.split('.')[-1]

    def __str__(self):
        return f"{self.name} > {self.sales_channel.hostname}"

    @classmethod
    def get_pending_tasks(cls, sales_channel):
        # Sum the number of remote requests for currently processing tasks
        processing_requests = cls.objects.filter(
            sales_channel=sales_channel,
            status=cls.PROCESSING
        ).aggregate(total=models.Sum('number_of_remote_requests'))['total'] or 0

        # Calculate the number of requests that can still be processed
        remaining_requests = sales_channel.requests_per_minute - processing_requests

        if remaining_requests > 0:
            # Get pending tasks, ordered by priority (high first) then by sent_to_queue_at
            pending_tasks = cls.objects.filter(
                sales_channel=sales_channel,
                status=cls.PENDING
            ).order_by('-priority', 'sent_to_queue_at')

            # Select tasks until the sum of their remote requests fits the remaining capacity
            selected_tasks = []
            total_requests = 0

            for task in pending_tasks:
                task_requests = task.number_of_remote_requests

                # if a task is bigger than the limit just add it. It will keep the queue full until is finished but at least will be processed
                if task_requests > sales_channel.requests_per_minute:
                    task.status = cls.PROCESSING
                    selected_tasks.append(task)
                    break

                if total_requests + task_requests <= remaining_requests:
                    task.status = cls.PROCESSING
                    selected_tasks.append(task)
                    total_requests += task_requests
                else:
                    break

            if selected_tasks:
                cls.objects.bulk_update(selected_tasks, ['status'])
            return selected_tasks

        return []

    def mark_as_processed(self):
        self.status = self.PROCESSED
        self.save()

    def mark_as_failed(self, error_message=None, error_traceback=None):
        self.retry += 1
        if self.retry < 3:
            self.status = self.PENDING
            self.sent_to_queue_at = now()  # Move to the back of the queue
        else:
            self.status = self.FAILED
            self.error_message = error_message
            self.error_traceback = error_traceback

        self.save()

    def dispatch(self):
        from sales_channels.helpers import resolve_function

        if self.status != self.PROCESSING:
            raise ValidationError("Cannot dispatch not proccessing tasks.")

        task_func = resolve_function(self.task_name)

        if task_func:
            logger.info(f"Dispatching task '{self.task_name}' for SalesChannel '{self.sales_channel.hostname}'.")
            # Pass task_queue_item_id, sales_channel_id, and relevant args to the task
            return task_func(
                self.id,
                *self.task_args,
                **self.task_kwargs
            )
        else:
            logger.error(f"Task '{self.task_name}' not found.")

    def retry_task(self, retry_now=False):
        self.retry = 0

        self.status = self.PROCESSING if retry_now else self.PENDING
        self.sent_to_queue_at = now()
        self.save()

        if retry_now:
            self.dispatch()