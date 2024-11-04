from core.documents import OneSilaBaseDocument
from contacts.models import InvoiceAddress, InternalCompany


class PrintOrder(OneSilaBaseDocument):
    def __init__(self, order):
        super().__init__()
        self.order = order
        self.multi_tenant_company = order.multi_tenant_company
        self.items = order.orderitem_set.all()
        self.shipping_address = order.shipping_address
        self.invoicing_address = order.invoice_address
        # FIXME: This should be dynamic from the order itself, but there is no
        # support as of yet.
        self.seller = order.internal_company
        self.seller_address = InvoiceAddress.objects.\
            get(
                company=self.seller,
                multi_tenant_company=self.multi_tenant_company
            )

    def add_address_headers(self):
        table_data = [
            ['Seller', 'Invoice To', 'Delivery At'],
            [self.seller_address.html(), self.invoicing_address.html(), self.shipping_address.html()],
        ]
        self.add_table(table_data, [0.33, 0.33, 0.33], line_under_header_row=False)
        self.add_vertical_space()

    def add_order_details(self):
        widths = [0.15, 0.25, 0.3, 0.3]
        reference = self.order.__str__()
        your_reference = self.order.reference
        date = self.order.created_at.date().isoformat()
        contact = "<br />".join([i for i in [self.seller.email, self.seller.phone] if i is not None]) or ''
        data = [
            ['Reference', 'Your Reference', 'Ordered on date', 'Contact'],
            [reference, your_reference, date, contact],
        ]
        self.add_table(data, widths, line_under_header_row=True, box_line=True)
        self.add_vertical_space()

    def add_items(self):
        widths = [0.2, 0.4, 0.1, 0.15, 0.15]
        data = [
            ['Article', 'Name', 'Qty', 'Price', 'Total'],
        ]

        for item in self.items:
            data.append([
                item.product.sku,
                item.product.name,
                item.quantity,
                item.price,
                item.subtotal_string(),
            ])

        # data.append([' ', ' ', ' ', ' ', ' '])
        # data.append([
        #     ' ',
        #     ' ',
        #     ' ',
        #     'Subtotal',
        #     self.order.total_value_string()
        # ])

        self.add_table(data, widths, bold_header_row=True, line_under_header_row=True,
            box_line=False, row_line=False)

    def generate(self):
        self.add_title(f"Order confirmation {self.order.__str__()}")
        self.add_vertical_space()
        self.add_address_headers()
        self.add_order_details()
        self.add_items()
        self.add_vertical_space()
        self.add_text("If you have any questions about this purchase order, please contact us.")

        super().generate()
