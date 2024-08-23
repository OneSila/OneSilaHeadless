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

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    received_on = models.DateField()
    status = models.CharField(max_length=18, choices=STATUS_CHOICES, default=ANNOUNCED)

    return_reason = models.TextField(null=True, blank=True)


class OrderReturnAttachment(models.Model):
    orderreturn = models.ForeignKey(OrderReturn, on_delete=models.CASCADE)
    file = models.FileField(_('File'),
        upload_to=get_orderreturn_attachment_folder_upload_path, validators=[validate_attachment_extensions, no_dots_in_filename],
        null=True, blank=True)


class OrderReturnItem(models.Model):
    orderreturn = models.ForeignKey(OrderReturn, on_delete=models.CASCADE)
    # NOTE: Must be limited by the items sold in the related order.
    orderitem = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
