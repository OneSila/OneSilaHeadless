from core import models
from core.validators import validate_pdf_extension
from django.utils.translation import gettext_lazy as _
from .documents import PickingListDocumentPrinter
from .managers import ShipmentItemManager
from .models_helpers import get_shippinglabel_folder_upload_path, \
    get_customs_document_folder_upload_path


class Shipment(models.SetStatusMixin, models.Model):
    """each for a given location"""
    DRAFT = "DRAFT"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"

    IN_PROGRESS_STATUS_LIST = [DRAFT, TODO, IN_PROGRESS]
    DONE_STATUS_LIST = [DONE, CANCELLED]

    STATUS_CHOICES = (
        (DRAFT, _("Draft")),
        (TODO, _("Todo")),
        (IN_PROGRESS, _("In Progress")),
        (DONE, _("Done")),
        (CANCELLED, _("Cancelled")),
    )

    RESERVED_STOCK_STATUSSES = [TODO, IN_PROGRESS]

    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default=DRAFT)
    from_address = models.ForeignKey('contacts.ShippingAddress', on_delete=models.PROTECT,
        related_name='shipments_from')
    to_address = models.ForeignKey('contacts.ShippingAddress', on_delete=models.PROTECT,
        related_name='shipments_to')

    # Can be set to null/blank to allow internal orders
    order = models.ForeignKey('orders.Order',
        on_delete=models.PROTECT,
        null=True,
        blank=True)

    @property
    def reference(self):
        return f"SH-{self.id}"

    def print(self):
        printer = PickingListDocumentPrinter(self)
        printer.generate()
        filename = f"{self.reference}.pdf"
        return filename, printer.pdf

    def print_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('shipments:shipment_pickinglist', kwargs={'pk': self.global_id})

    def set_status_todo(self):
        self.set_status(self.TODO)

    def set_status_done(self):
        self.set_status(self.DONE)

    def is_draft(self):
        return self.status == self.DRAFT

    def is_todo(self):
        return self.status == self.TODO

    def is_in_progress(self):
        return self.status == self.IN_PROGRESS

    def is_done(self):
        return self.status == self.DONE

    def is_cancelled(self):
        return self.status == self.CANCELLED


class ShipmentItem(models.Model):
    """Shipment item to be used to determine how many items have been shipped in an order
    of the actually sold product"""
    shipments = models.ManyToManyField(Shipment, blank=True)
    orderitem = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()

    objects = ShipmentItemManager()


class ShipmentItemToShip(models.Model):
    """ Shipment items are auto-populated based on availablity for a given location"""
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    quantity = models.IntegerField()
    shipment = models.ForeignKey(Shipment, on_delete=models.PROTECT)
    orderitem = models.ForeignKey('orders.OrderItem', on_delete=models.PROTECT)
    inventorylocation = models.ForeignKey('inventory.InventoryLocation', on_delete=models.PROTECT)


class Package(models.SetStatusMixin, models.Model):
    BOX = "BOX"
    PALLET = "PALLET"

    TYPE_CHOICES = (
        (BOX, _("Box")),
        (PALLET, _("Pallet")),
    )

    NEW = 'NEW'
    IN_PROGRESS = 'IN_PROGRESS'
    PACKED = 'PACKED'
    DISPATCHED = 'DISPATCHED'

    STATUS_CHOICES = (
        (NEW, _("New")),
        (IN_PROGRESS, _("In Progress")),
        (PACKED, _("Packed")),
        (DISPATCHED, _("Dispatched")),
    )
    RESERVED_STOCK_STATUSSES = [IN_PROGRESS]

    type = models.CharField(max_length=6, choices=TYPE_CHOICES)
    shipment = models.ForeignKey(Shipment, on_delete=models.PROTECT)

    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default=NEW)

    tracking_code = models.CharField(max_length=254, blank=True, null=True)
    tracking_link = models.URLField(blank=True, null=True, max_length=254)
    shipping_label = models.FileField(upload_to=get_shippinglabel_folder_upload_path,
        validators=[validate_pdf_extension], blank=True, null=True)
    customs_document = models.FileField(upload_to=get_customs_document_folder_upload_path,
        validators=[validate_pdf_extension], blank=True, null=True)

    def set_status_new(self):
        self.set_status(self.NEW)

    def set_status_in_progress(self):
        self.set_status(self.IN_PROGRESS)

    def set_status_packed(self):
        self.set_status(self.PACKED)

    def set_status_dispatched(self):
        self.set_status(self.DISPATCHED)

    def is_new(self):
        return self.status == self.NEW

    def is_in_progress(self):
        return self.status == self.IN_PROGRESS

    def is_packed(self):
        return self.status == self.PACKED

    def is_dispatched(self):
        return self.status == self.DISPATCHED


class PackageItem(models.Model):
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    inventory = models.ForeignKey('inventory.Inventory', on_delete=models.PROTECT)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.IntegerField()
