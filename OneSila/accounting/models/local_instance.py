from decimal import Decimal

from accounting.helpers import get_credit_note_pdf_upload_path, get_invoice_pdf_upload_path
from accounting.models.mixins import DocumentBase, DocumentItemBase
from core import models

class Invoice(DocumentBase):
    due_date = models.DateField(blank=True, null=True)
    sales_order = models.ForeignKey('orders.Order', on_delete=models.PROTECT)
    invoice_pdf = models.FileField(upload_to=get_invoice_pdf_upload_path, blank=True, null=True)

    def __str__(self):
        return f"Invoice {self.document_number}"


class InvoiceItem(DocumentItemBase):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.PROTECT, related_name='invoice_items')

    def __str__(self):
        return f"{self.name} (Invoice {self.invoice.document_number})"

    @property
    def line_total(self):
        """
        Calculate the total for this line item (quantity * unit price).
        """
        return Decimal(self.quantity) * Decimal(self.unit_price)


class CreditNote(DocumentBase):
    order_return = models.ForeignKey('order_returns.OrderReturn', on_delete=models.PROTECT)
    credit_note_pdf = models.FileField(upload_to=get_credit_note_pdf_upload_path)

    def __str__(self):
        return f"Credit Note {self.document_number}"


class CreditNoteItem(DocumentItemBase):
    credit_note = models.ForeignKey(CreditNote, on_delete=models.CASCADE, related_name='items')
    order_return_item = models.ForeignKey('order_returns.OrderReturnItem', on_delete=models.PROTECT, related_name='credit_note_items')

    def __str__(self):
        return f"{self.name} (Credit Note {self.credit_note.document_number})"