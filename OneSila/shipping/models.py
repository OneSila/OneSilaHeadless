from core import models
from core.validators import validate_pdf_extension
from django.utils.translation import gettext_lazy as _
from .models_helpers import get_customs_document_folder_upload_path, \
    get_customs_document_folder_upload_path


class Shipment(models.Model):
    from_address = models.ForeignKey('contacts.ShippingAddress', on_delete=models.PROTECT)
    to_address = models.ForeignKey('contacts.ShippingAddress', on_delete=models.PROTECT)

    # Can be set to null/blank to allow internal orders
    order = models.ForeignKey('orders.SalesOrder',
        on_delete=models.PROTECT,
        null=True,
        blank=True
                              )


class Package(models.Model):
    BOX = "BOX"
    PALLET = "PALLET"

    TYPE_CHOICES = (
        (BOX, _("Box")),
        (PALLET, _("Pallet")),
    )

    NEW = 'NEW'
    IN_PROGRESS = 'IN_PROGRESS'
    PACKAGED = 'PACKAGED'
    DISPATCHED = 'DISPATCHED'

    STATUS_CHOICES = (
        (NEW, _("New")),
        (IN_PROGRESS, _("In Progress")),
        (PACKAGED, _("Packaged")),
        (DISPATCHED, _("Dispatched")),
    )

    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    shipment = models.ForeignKey(Shipment, on_delete=models.PROTECT)

    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default=NEW)

    tracking_code = models.CharField(max_length=254, blank=True, null=True)
    tracking_link = models.URLField(blank=True, null=True, max_length=254)
    shipping_label = models.FileField(upload_to=get_shippinglabel_folder_upload_path,
        validators=[validate_pdf_extension], blank=True, null=True)
    customs_document = models.FileField(upload_to=get_customs_document_folder_upload_path,
        validators=[validate_pdf_extension], blank=True, null=True)


class PackageItem(models.Model):
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    qty = models.IntegerField()
