from accounting.models import Invoice
from core.documents import OneSilaBaseDocument


class GenerateDocument(OneSilaBaseDocument):
    def __init__(self, document):
        super().__init__()
        self.document = document
        self.items = document.items.all()  # InvoiceItem or CreditNoteItem based on the document

        # Vendor (seller) information
        self.vendor_name = document.vendor_name
        self.vendor_address = document.vendor_address
        self.vendor_email = document.vendor_email
        self.vendor_phone = document.vendor_phone
        self.vendor_vat_number = document.vendor_vat_number
        self.order_number = document.order_number

        # Customer information
        self.customer_name = document.customer_name
        self.customer_invoice_address = document.customer_invoice_address
        self.customer_shipping_address = document.customer_shipping_address
        self.customer_email = document.customer_email
        self.customer_phone = document.customer_phone
        self.customer_vat_number = document.customer_vat_number

        self.document_number = document.document_number
        self.document_date = document.document_date
        self.due_date = getattr(document, 'due_date', None)
        self.currency_symbol = document.currency_symbol

    def add_address_headers(self):
        # Add Vendor and Customer Information
        vendor_elements = [
            self.vendor_name,
            self.vendor_address,
            f"Email: {self.vendor_email}" if self.vendor_email else None,
            f"Phone: {self.vendor_phone}" if self.vendor_phone else None,
            f"VAT: {self.vendor_vat_number}" if self.vendor_vat_number else None
        ]

        customer_elements = [
            self.customer_name,
            self.customer_invoice_address,
            f"Email: {self.customer_email}" if self.customer_email else None,
            f"Phone: {self.customer_phone}" if self.customer_phone else None,
            f"VAT: {self.customer_vat_number}" if self.customer_vat_number else None
        ]

        # Join the elements with newline (\n) instead of <br>
        vendor_info = "\n".join(filter(None, vendor_elements))
        customer_info = "\n".join(filter(None, customer_elements))

        # Prepare table data
        table_data = [
            ['Vendor', 'Invoice to'],
            [vendor_info, customer_info],
        ]

        # Add table without using HTML tags
        self.add_table(table_data, [0.5, 0.5], line_under_header_row=False)
        self.add_vertical_space()

    def add_order_details(self):
        # Add document metadata like document number, date, and due date (if applicable)
        document_date = self.document.document_date.strftime('%d %B %Y')
        due_date = self.due_date.strftime('%d %B %Y') if self.due_date else 'N/A'

        data = [
            ['Order reference', 'Document Date', 'Due Date'],
            [self.order_number, document_date, due_date],
        ]
        self.add_table(data, [0.33, 0.33, 0.33], line_under_header_row=True, box_line=True)
        self.add_vertical_space()

    def add_items(self):
        # Add Items Table: Nr, Article, Quantity, Price, Total Price, VAT Rate, VAT Amount
        table_headers = ['Nr', 'Article', 'Qty', 'Price per Qty', 'Total Price', 'VAT Rate', 'Tax Amount']
        table_data = [table_headers]
        widths = [0.05, 0.25, 0.1, 0.15, 0.15, 0.15, 0.15]

        for index, item in enumerate(self.items, start=1):
            line_total = item.line_total
            tax_amount = item.tax_amount
            table_data.append([
                str(index),
                item.name,
                item.quantity,
                f"{item.unit_price} {self.currency_symbol}",
                f"{line_total} {self.currency_symbol}",
                f"{item.preserved_vat_rate}%",
                f"{tax_amount} {self.currency_symbol}"
            ])

        self.add_table(table_data, widths, bold_header_row=True, line_under_header_row=True)
        self.add_vertical_space()

    def add_totals(self):
        # Add Subtotal, Tax Amount, and Total
        subtotal = self.document.subtotal
        tax_amount = self.document.tax_amount
        total = self.document.total

        fake_line = [
            [' ', ' ']
        ]
        self.add_table(fake_line, [0.7, 0.3], line_under_header_row=True, box_line=False)

        table_data = [
            ['Subtotal', f"{subtotal} {self.currency_symbol}"],
            ['Tax Amount', f"{tax_amount} {self.currency_symbol}"],
        ]
        self.add_table(table_data, [0.7, 0.3], line_under_header_row=False, box_line=False)

        table_data_total = [
            ['Total', f"{total} {self.currency_symbol}"]
        ]
        self.add_table(table_data_total, [0.7, 0.3], line_under_header_row=False, box_line=True)

        self.add_vertical_space()



    def generate(self):
        # Add title depending on document type
        document_type = "Invoice" if isinstance(self.document, Invoice) else "Credit Note"
        self.add_title(f"{document_type} {self.document.document_number}")
        self.add_vertical_space()

        # Add document content
        self.add_address_headers()  # Vendor and Customer Information
        self.add_order_details()    # Document Metadata (Number, Date, Due Date)
        self.add_items()            # Items (Nr, Article, Qty, Price, VAT)
        self.add_vertical_space()   # add some space
        self.add_vertical_space()
        self.add_totals()           # Totals (Subtotal, Tax, Total)

        super().generate()
