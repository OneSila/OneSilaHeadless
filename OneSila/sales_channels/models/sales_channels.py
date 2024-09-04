from django.core.exceptions import ValidationError

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
    price_list = models.ForeignKey('prices.PriceList', on_delete=models.PROTECT)
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

    STATUS_DRAFT = 'DRAFT'
    STATUS_PENDING = 'PENDING'
    STATUS_TODO = 'TODO'
    STATUS_DONE = 'DONE'
    STATUS_FAILED = 'FAILED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_TODO, 'To Do'),
        (STATUS_DONE, 'Done'),
        (STATUS_FAILED, 'Failed'),
    ]

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, db_index=True)
    sales_channel_view = models.ForeignKey('SalesChannelView', on_delete=models.CASCADE, db_index=True)
    remote_product = models.ForeignKey('sales_channels.RemoteProduct', on_delete=models.SET_NULL, null=True, blank=True, help_text="The remote product associated with this assign.")
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    needs_resync = models.BooleanField(default=False, help_text="Indicates if a resync is needed.")

    class Meta:
        unique_together = ('product', 'sales_channel_view')
        verbose_name = 'Sales Channel View Assign'
        verbose_name_plural = 'Sales Channel View Assigns'
        ordering = ('product_id', 'sales_channel_view__name')

    def __str__(self):
        return f"{self.product} @ {self.sales_channel_view}"

    def set_pending(self, save=True):
        self.set_status(self.STATUS_PENDING, save)

    def set_todo(self, save=True):
        self.set_status(self.STATUS_TODO, save)

    def set_done(self, save=True):
        self.set_status(self.STATUS_DONE, save)

    def set_failed(self, save=True):
        self.set_status(self.STATUS_FAILED, save)

    def set_status(self, status, save=True):
        """
        Generic method to set the status of the assignment.
        """
        self.status = status
        if save:
            self.save()

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
    task_args = models.JSONField()
    task_kwargs = models.JSONField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    sent_to_queue_at = models.DateTimeField(default=now)
    retry = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    error_traceback = models.TextField(null=True, blank=True)
    number_of_remote_requests = models.IntegerField(default=1) # how many remote requests does this task do?
    priority = models.IntegerField(default=DEFAULT_PRIORITY)

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

    def mark_as_failed(self):
        self.retry += 1
        if self.retry < 3:
            self.status = self.PENDING
            self.sent_to_queue_at = now()  # Move to the back of the queue
        else:
            self.status = self.FAILED
        self.save()

    def dispatch(self):
        if self.status != self.PROCESSING:
            raise ValidationError("Cannot dispatch not proccessing tasks.")

        task_func = globals().get(self.task_name)
        if task_func:
            logger.info(f"Dispatching task '{self.task_name}' for SalesChannel '{self.sales_channel.name}'.")
            # Pass task_queue_item_id, sales_channel_id, and relevant args to the task
            task_func(
                self.id,
                *self.task_args,
                **self.task_kwargs
            )
        else:
            logger.error(f"Task '{self.task_name}' not found.")

    def retry(self, retry_now=False):
        self.retry = 0

        if retry_now:
            self.status = self.PROCESSING
        else:
            self.status = self.PENDING


        self.sent_to_queue_at = now()
        self.save()

        if retry_now:
            self.dispatch()