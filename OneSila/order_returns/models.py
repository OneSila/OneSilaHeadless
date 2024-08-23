from core import models
from django.utils.translation import gettext_lazy as _


class OrderReturn(models.Model):
    ANNOUNCED = 'ANNOUNCED'
    RECEIVED = 'RECEIVED'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    REJECTED = 'REJECTED'
    PENDING_REPAYMENT = 'PENDING_REPAYMENT'
    REFUNDED = 'REFUNDED'

    STATUS_CHOICES = (
        (ANNOUNCED, _("Announced")),
        (RECEIVED, _("Received")),
        (PENDING_APPROVAL, _("Pending Approval")),
        (REJECTED, _("Rejected")),
        (PENDING_REPAYMENT, _("Pending Repayment")),
        (REFUNDED, _("Refunded")),
    )

    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    received_on = models.DateField()
    status = models.CharField(max_length=17, choices=STATUS_CHOICES, default=ANNOUNCED)

    return_reason = models.TextField(null=True, blank=True)


class OrderReturnItem(models.Model):
    # NOTE: Must be limited by the items sold in the related order.
    orderitem = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
