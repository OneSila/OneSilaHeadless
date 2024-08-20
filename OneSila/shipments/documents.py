from core.documents import OneSilaBaseDocument
from contacts.models import InvoiceAddress
from inventory.models import InventoryLocation


class PickingListDocumentPrinter(OneSilaBaseDocument):
    def __init__(self, shipment):
        super().__init__()
        self.shipment = shipment
        self.order = shipment.order
        self.shipping_address = shipment.from_address
        self.multi_tenant_company = shipment.multi_tenant_company
        self.shipmentitems = shipment.shipmentitemtoship_set.all()
        self.customer = shipment.order.customer

    # def add_address_headers(self, supplier, invoice_address, delivery_address):
    #     table_data = [
    #         ['Vendor', 'Invoice To', 'Delivery At'],
    #         [supplier, invoice_address, delivery_address],
    #     ]
    #     self.add_table(table_data, [0.33, 0.33, 0.33], line_under_header_row=False)
    #     self.add_vertical_space()

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
        widths = [0.25, 0.25, 0.35, 0.15]
        data = [
            ['Location', 'Sku', 'Description', 'Qty'],
        ]

        for item in self.shipmentitems:
            product = item.product
            picking_locations = product.inventory.\
                determine_picking_locations(product, self.shipping_address, item.quantity)

            for location, qty in picking_locations.items():
                data.append([
                    location.inventorylocation.name,
                    product.sku,
                    product.name,
                    qty
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
        self.add_title(f"Picking List {self.shipment.reference}")
        self.add_vertical_space()
        # self.add_address_headers(
        #     supplier=self.get_supplier_html(),
        #     invoice_address=self.invoicing_address.html(),
        #     delivery_address=self.shipping_address.html())
        self.add_shipment_details()
        self.add_items()
        self.add_vertical_space()
        # self.add_text("If you have any questions about this purchase order, please contact us.")

        super().generate()
