from decimal import Decimal, ROUND_HALF_UP
from accounting.models.local_instance import Invoice, CreditNote
from accounting.models.remote_instance import AccountingMirrorAccount
from core.helpers import get_nested_attr
from datetime import timedelta
from django.utils import timezone

class DocumentCreateFactoryMixin:
    local_class = None  # The model class for Invoice or CreditNote
    local_item_class = None  # The model for the items (e.g., InvoiceItem or CreditNoteItem)
    field_map = {}  # Mapping from instance fields to document fields
    item_field_map = {}  # Mapping from instance item fields to document item fields
    internal_company_map = None  # Mapping for how we get the internal company from the instance
    get_items_method = None  # Method to retrieve items from the instance
    generate_document_factory = None  # Factory to generate the document PDF
    signal_to_trigger = None  # Signal to trigger after document creation

    def __init__(self, instance):
        self.instance = instance
        self.payload = {}
        self.document = None
        self.internal_company = get_nested_attr(self.instance, self.internal_company_map)


    def fetch_vendor_details(self):
        """
        Fetch vendor details from InternalCompany based on multi_tenant_company.
        """

        if not self.internal_company:
            raise ValueError("No InternalCompany found for this multi_tenant_company")

        # Fetch first invoice and shipping addresses
        invoice_address = self.internal_company.address_set.filter(is_invoice_address=True).first()

        vendor_details = {
            'vendor_name': self.internal_company.name,
            'vendor_address': invoice_address.html() if invoice_address else '',
            'vendor_email': self.internal_company.email,
            'vendor_phone': self.internal_company.phone,
            'vendor_vat_number': invoice_address.vat_number if invoice_address else '',
        }

        return vendor_details

    def build_payload(self):
        """
        Construct the payload for creating the document using the provided field mapping.
        Supports nested fields using '__' notation.
        """
        for local_field, document_field in self.field_map.items():
            self.payload[document_field] = get_nested_attr(self.instance, local_field)

        vendor_details = self.fetch_vendor_details()
        self.payload.update(vendor_details)

        # Check if document_number is None, and generate if necessary
        if not self.payload.get('document_number') or self.local_class == CreditNote:
            self.payload['document_number'] = self.generate_reference()

        return self.payload

    def generate_reference(self):
        """
        Generate a reference for the document if none exists.
        Use different prefixes based on whether it's an Invoice or CreditNote.
        """
        if self.local_class == Invoice:
            prefix = 'INV'
            cnt = Invoice.objects.filter(sales_order__internal_company=self.internal_company).count() + 1
        else:
            prefix = 'CRN'
            cnt = CreditNote.objects.filter(order_return__order__internal_company=self.internal_company).count() + 1

        return f"{prefix}-{str(cnt).zfill(7)}"

    def set_due_data_if_neccessary(self, document_data):
        account = AccountingMirrorAccount.objects.filter(internal_company=self.internal_company).first()
        if self.local_class == Invoice and account is not None:
            document_data['due_date'] = timezone.now().date() + timedelta(days=account.due_days)

        return document_data

    def create_document(self):
        """
        Create the document (Invoice/CreditNote) and save it.
        """
        related_instance_key = 'sales_order' if self.local_class == Invoice else 'order_return'
        document_data = {
            'multi_tenant_company': self.instance.multi_tenant_company,
            related_instance_key: self.instance,
            **self.payload
        }

        document_data = self.set_due_data_if_neccessary(document_data)
        self.document = self.local_class.objects.create(**document_data)

    def create_document_items(self):
        price_incl_vat = getattr(self.document, 'price_incl_vat', True)
        subtotal = Decimal(0)
        total_tax_amount = Decimal(0)

        items = getattr(self.instance, self.get_items_method).all()
        for item in items:
            # Use 'invoice' or 'credit_note' based on context
            document_key = 'invoice' if self.local_class == Invoice else 'credit_note'
            item_key = 'order_item' if self.local_class == Invoice else 'order_return_item'
            item_data = {
                document_key: self.document,
                item_key: item,
                'name': f"{item.product.name} ({item.product.sku})",
                'multi_tenant_company': self.instance.multi_tenant_company
            }

            for item_local_field, item_document_field in self.item_field_map.items():
                item_data[item_document_field] = get_nested_attr(item, item_local_field)

            if item_data['preserved_vat_rate'] is None:
                item_data['preserved_vat_rate'] = 0

            # Calculate tax amount based on whether price includes VAT and the full line amount
            item_data['tax_amount'], line_total = self.calculate_tax_amount(item_data, price_incl_vat)

            # Store item and calculate line totals
            self.local_item_class.objects.create(**item_data)

            # Accumulate subtotal and total tax amount
            if price_incl_vat:
                subtotal += line_total / (Decimal(1) + Decimal(item_data['preserved_vat_rate']) / Decimal(100))
            else:
                subtotal += line_total

            total_tax_amount += item_data['tax_amount']

        precision = Decimal('0.01')

        # Round the calculated values using quantize with ROUND_HALF_UP
        self.document.subtotal = subtotal.quantize(precision, rounding=ROUND_HALF_UP)
        self.document.tax_amount = total_tax_amount.quantize(precision, rounding=ROUND_HALF_UP)
        self.document.total = (self.document.subtotal + self.document.tax_amount).quantize(precision, rounding=ROUND_HALF_UP)
        self.document.save()


    def calculate_tax_amount(self, item_data, price_incl_vat):
        """
        Calculate the tax amount for the item based on whether the price includes VAT.
        This calculation is done for the entire line (quantity * unit_price).
        """
        quantity = Decimal(item_data['quantity'])
        unit_price = Decimal(item_data['unit_price'])
        vat_rate = Decimal(item_data['preserved_vat_rate']) / Decimal(100)

        line_total = quantity * unit_price

        if price_incl_vat:
            # If the price includes VAT, extract the VAT from the total price
            line_total_excl_vat = line_total / (Decimal(1) + vat_rate)
            tax_amount = line_total - line_total_excl_vat
        else:
            # If the price excludes VAT, calculate the VAT on top of the total price
            tax_amount = line_total * vat_rate

        return tax_amount, line_total

    def generate_document_pdf(self):
        """
        Run the GenerateDocument factory to create the PDF.
        """
        self.generate_document_factory(self.document).run()

    def send_signal(self):
        """
        Trigger the signal to indicate that the document has been created.
        """
        self.signal_to_trigger.send(sender=self.local_class, instance=self.document)

    def run(self):
        """
        Orchestrate the full document creation process.
        """
        self.build_payload()
        self.create_document()
        self.create_document_items()
        self.generate_document_pdf()
        self.send_signal()