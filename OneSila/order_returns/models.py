from decimal import Decimal

from core import models
from core.validators import validate_attachment_extensions, no_dots_in_filename
from .helpers import get_orderreturn_attachment_folder_upload_path
from django.utils.translation import gettext_lazy as _


class OrderReturn(models.Model):
    ANNOUNCED = 'ANNOUNCED'
    RECEIVED = 'RECEIVED'
    PENDING_INSPECTION = 'PENDING_INSPECTION'
    REJECTED = 'REJECTED'
    PENDING_REPAYMENT = 'PENDING_REPAYMENT'
    REFUNDED = 'REFUNDED'

    STATUS_CHOICES = (
        (ANNOUNCED, _("Announced")),
        (RECEIVED, _("Received")),
        (PENDING_INSPECTION, _("Pending Inspection")),
        (REJECTED, _("Rejected")),
        (PENDING_REPAYMENT, _("Pending Repayment")),
        (REFUNDED, _("Refunded")),
    )

    OPEN_STATUSES = [ANNOUNCED]

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    received_on = models.DateField()
    status = models.CharField(max_length=18, choices=STATUS_CHOICES, default=ANNOUNCED)
    tracking_url = models.URLField(null=True, blank=True)
    return_reason = models.TextField(null=True, blank=True)

    @property
    def total_value(self):
        """
        Calculate the total value of the entire return by summing up the total values
        of the associated OrderReturnItems.
        """
        return sum(item.total_value for item in self.orderreturnitem_set.all())

class OrderReturnAttachment(models.Model):
    order_return = models.ForeignKey(OrderReturn, on_delete=models.CASCADE)
    file = models.FileField(_('File'),
        upload_to=get_orderreturn_attachment_folder_upload_path, validators=[validate_attachment_extensions, no_dots_in_filename],
        null=True, blank=True)


class OrderReturnItem(models.Model):
    order_return = models.ForeignKey(OrderReturn, on_delete=models.CASCADE)
    # NOTE: Must be limited by the items sold in the related order.
    # @TODO: Add a validation error quantity cannot be bigger than orderitem.quantity
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()

    @property
    def total_value(self):
        """
        Calculate the total value of the returned items based on the price and quantity.
        """
        return Decimal(self.order_item.price) * Decimal(self.quantity)