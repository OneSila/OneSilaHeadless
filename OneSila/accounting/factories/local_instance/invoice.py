from django.core.files.base import ContentFile

from accounting.documents import GenerateDocument
from accounting.factories.local_instance.mixins import DocumentCreateFactoryMixin
from accounting.models.local_instance import Invoice, InvoiceItem
from accounting.signals import create_remote_invoice


class GenerateInvoiceFileFactory:

    def __init__(self, invoice):
        self.invoice = invoice

    def generate_invoice_file(self):
        self.pdf_generator = GenerateDocument(self.invoice)
        self.pdf_generator.generate()

    def add_to_instance(self):
        self.invoice.invoice_pdf.save(f"invoice_{self.invoice.document_number}.pdf", ContentFile(self.pdf_generator.pdf))

    def run(self):
        self.generate_invoice_file()
        self.add_to_instance()

class InvoiceCreateFactory(DocumentCreateFactoryMixin):
    local_class = Invoice
    local_item_class = InvoiceItem
    field_map = {
        'reference': 'order_number',
        'created_at': 'document_date',
        'customer__name': 'customer_name',
        'invoice_address__full_address': 'customer_invoice_address',
        'shipping_address__full_address': 'customer_shipping_address',
        'customer__email': 'customer_email',
        'customer__phone': 'customer_phone',
        'invoice_address__vat_number': 'customer_vat_number',
        'currency__symbol': 'currency_symbol',
        'price_incl_vat': 'price_incl_vat'
    }
    item_field_map = {
        'quantity': 'quantity',
        'price': 'unit_price',
        'product__vat_rate': 'vat_rate',
        'product__vat_rate__rate': 'preserved_vat_rate'
    }
    internal_company_map = 'internal_company'
    get_items_method = 'orderitem_set'
    generate_document_factory = GenerateInvoiceFileFactory
    signal_to_trigger = create_remote_invoice

