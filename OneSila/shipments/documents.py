from core.documents import OneSilaBaseDocument


class PickingListDocumentPrinter(OneSilaBaseDocument):
    def __init__(self, shipment):
        super().__init__()
        self.shipment = shipment
        self.order = shipment.order
        self.shipping_address = shipment.from_address
        self.multi_tenant_company = shipment.multi_tenant_company
        self.shipmentitems = shipment.shipmentitemtoship_set.all()
        self.customer = shipment.order.customer

    def add_shipment_details(self):
        widths = [0.4, 0.3, 0.3]
        reference = self.order.reference
        customer_name = self.order.customer.name
        date = self.shipment.created_at.date().isoformat()
        data = [
            ['Order #', 'Shipment Date', 'Customer'],
            [reference, date, customer_name],
        ]
        self.add_table(data, widths, line_under_header_row=True, box_line=True)
        self.add_vertical_space()

    def add_items(self):
        widths = [0.05, 0.2, 0.15, 0.25, 0.35]
        data = [
            ['', 'Location', 'Qty', 'Sku', 'Product Name'],
        ]

        for item in self.shipmentitems:
            product = item.product
            picking_locations = product.inventory.\
                determine_picking_locations(product, self.shipping_address, item.quantity)

            for location, qty in picking_locations.items():
                data.append([
                    '☐',
                    location.inventorylocation.name,
                    qty,
                    product.sku,
                    product.name,
                ])

        self.add_table(data, widths, bold_header_row=True, line_under_header_row=True,
            box_line=False, row_line=False)

    def generate(self):
        self.add_title(f"Picking List {self.shipment.reference}")
        self.add_vertical_space()
        self.add_shipment_details()
        self.add_items()
        self.add_vertical_space()
        # self.add_text("If you have any questions about this purchase order, please contact us.")

        super().generate()
