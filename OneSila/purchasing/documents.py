from core.documents import OneSilaBaseDocument
from contacts.models import InvoiceAddress


class PrintPurchaseOrder(OneSilaBaseDocument):
    def __init__(self, purchaseorder):
        super().__init__()
        self.purchaseorder = purchaseorder
        self.multi_tenant_company = purchaseorder.multi_tenant_company
        self.supplier = purchaseorder.supplier
        self.items = purchaseorder.purchaseorderitem_set.all()
        self.shipping_address = purchaseorder.shipping_address
        self.invoicing_address = purchaseorder.invoice_address

    def add_address_headers(self, supplier, invoice_address, delivery_address):
        table_data = [
            ['Vendor', 'Invoice To', 'Delivery At'],
            [supplier, invoice_address, delivery_address],
        ]
        self.add_table(table_data, [0.33, 0.33, 0.33], line_under_header_row=False)
        self.add_vertical_space()

    def add_po_details(self):
        widths = [0.2, 0.2, 0.3, 0.3]
        reference = self.purchaseorder.order_reference
        date = self.purchaseorder.created_at.date().isoformat()
        user = self.purchaseorder.internal_contact
        user_contact = "<br />".join([i for i in [user.email, user.mobile_number] if i is not None]) or ''
        data = [
            ['PO Reference', 'Ordered on date', 'Contact', 'Email'],
            [reference, date, user.full_name(), ],
        ]
        self.add_table(data, widths, line_under_header_row=True, box_line=True)
        self.add_vertical_space()

    def add_items(self):
        widths = [0.2, 0.4, 0.1, 0.15, 0.15]
        data = [
            ['Article', 'Description', 'Qty', 'Unit Price', 'Total'],
        ]

        for item in self.items:
            data.append([
                item.product.sku,
                item.product.name,
                item.quantity,
                item.unit_price_string(),
                item.subtotal_string(),
            ])

        data.append([' ', ' ', ' ', ' ', ' '])
        data.append([
            ' ',
            ' ',
            ' ',
            'Subtotal',
            self.purchaseorder.total_value_string()
        ])

        self.add_table(data, widths, bold_header_row=True, line_under_header_row=True,
            box_line=False, row_line=False)

    def get_supplier_html(self):
        try:
            invoice_address = InvoiceAddress.objects.get(
                multi_tenant_company=self.multi_tenant_company,
                company=self.supplier)
            return invoice_address.html()
        except InvoiceAddress.DoesNotExist:
            return self.supplier.html()

    def generate(self):
        self.add_title(f"Purchase order from {self.invoicing_address.company.name}")
        self.add_vertical_space()
        self.add_address_headers(
            supplier=self.get_supplier_html(),
            invoice_address=self.invoicing_address.html(),
            delivery_address=self.shipping_address.html())
        self.add_po_details()
        self.add_items()
        self.add_vertical_space()
        self.add_text("If you have any questions about this purchase order, please contact us.")

        super().generate()
