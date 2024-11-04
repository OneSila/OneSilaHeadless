from quickbooks.objects import Invoice, SalesItemLine, Ref, SalesItemLineDetail, EmailAddress, TxnTaxDetail, TaxLine, TaxLineDetail
from accounting.factories.remote_instance.remote_instance import RemoteInvoiceCreateFactory
from accounting.integrations.quickbooks.factories import GetQuickbooksAPIMixin, GetOrCreateQuickbooksCustomerMixin, GetCreateOrUpdateItemMixin
from accounting.integrations.quickbooks.models import QuickbooksInvoice, QuickbooksVat

class QuickbooksInvoiceCreateFactory(GetQuickbooksAPIMixin, GetOrCreateQuickbooksCustomerMixin, GetCreateOrUpdateItemMixin, RemoteInvoiceCreateFactory):
    remote_model_class = QuickbooksInvoice

    field_mapping = {
        'document_number': 'DocNumber',
    }

    def __init__(self, remote_account, local_instance, api=None):
        self.customer = local_instance.sales_order.customer
        self.sales_order = local_instance.sales_order

        super().__init__(remote_account, local_instance, api)

    def get_remote_vat(self, product):
        local_vat = product.vat_rate

        if local_vat is None:
            raise Exception("Remote vat not found")

        try:
            remote_vat = QuickbooksVat.objects.get(local_instance=local_vat, remote_account=self.remote_account)
        except QuickbooksVat.DoesNotExist:
            remote_vat = QuickbooksVat.objects.filter(remote_account=self.remote_account).first()

        if remote_vat is None:
            raise Exception("Remote vat not found")

        return remote_vat

    def create_remote(self):
        """
        Custom logic to create an invoice in QuickBooks using the SDK.
        Includes handling line items.
        """
        qb_invoice = Invoice()

        for local_field, remote_field in self.field_mapping.items():
            setattr(qb_invoice, remote_field, getattr(self.local_instance, local_field, None))

        qb_invoice.TotalAmt = float(self.local_instance.total)
        qb_invoice.CustomerRef = self.get_quickbooks_customer().to_ref()

        if self.local_instance.due_date:
            qb_invoice.DueDate = self.local_instance.due_date.strftime('%Y-%m-%d')

        if self.local_instance.document_date:
            qb_invoice.TxnDate = self.local_instance.document_date.strftime('%Y-%m-%d')

        if self.local_instance.price_incl_vat:
            qb_invoice.GlobalTaxCalculation = "TaxInclusive"
        else:
            qb_invoice.GlobalTaxCalculation = "TaxExcluded"

        if self.sales_order.invoice_address:
            qb_invoice.BillAddr = self.map_address(self.sales_order.invoice_address)

        if self.sales_order.shipping_address:
            qb_invoice.ShipAddr = self.map_address(self.sales_order.shipping_address)

        if self.customer.email:
            qb_invoice.BillEmail = EmailAddress()
            qb_invoice.BillEmail.Address = self.customer.email

        tax_code_ref = None
        if self.remote_account.code_of_service:
            tax_code_ref = Ref()
            tax_code_ref.value = self.remote_account.code_of_service
            tax_code_ref.name = self.remote_account.code_of_service
            tax_code_ref.type = 'TaxCode'

        line_num_counter = 1
        total_tax = 0.0
        tax_summary = {}

        for line_item in self.local_instance.items.all():
            qb_line = SalesItemLine()
            qb_line.DetailType = "SalesItemLineDetail"
            qb_line.Description = line_item.name
            qb_line.Amount = float(line_item.line_total)
            qb_line.LineNum = line_num_counter

            item = self.get_or_create_item(line_item, line_item.order_item.product)
            detail = SalesItemLineDetail()
            detail.ItemRef = item.to_ref()
            detail.Qty = line_item.quantity
            detail.UnitPrice = float(line_item.unit_price)

            product = line_item.order_item.product
            local_vat = product.vat_rate

            try:
                remote_vat = self.get_remote_vat(product)
            except Exception as e:
                raise Exception(f"Tax code not found for product {product}: {e}")

            tax_code_ref = Ref()
            tax_code_ref.value = remote_vat.remote_id
            detail.TaxCodeRef = tax_code_ref

            qb_line.SalesItemLineDetail = detail
            qb_invoice.Line.append(qb_line)

            vat_percentage = local_vat.rate
            line_amount = float(line_item.line_total)

            if self.local_instance.price_incl_vat:
                net_amount = line_amount / (1 + vat_percentage / 100)
                tax_amount = line_amount - net_amount
            else:
                net_amount = line_amount
                tax_amount = net_amount * vat_percentage / 100

            total_tax += tax_amount

            tax_rate_ref = remote_vat.tax_rate_id

            if tax_rate_ref not in tax_summary:
                tax_summary[tax_rate_ref] = {
                    'NetAmountTaxable': 0.0,
                    'TaxAmount': 0.0,
                    'TaxPercent': vat_percentage,
                    'TaxRateRef': tax_rate_ref
                }

            tax_summary_entry = tax_summary[tax_rate_ref]
            tax_summary_entry['NetAmountTaxable'] += net_amount
            tax_summary_entry['TaxAmount'] += tax_amount

            line_num_counter += 1

        txn_tax_detail = TxnTaxDetail()
        txn_tax_detail.TotalTax = total_tax
        txn_tax_detail.TaxLine = []

        for entry in tax_summary.values():
            tax_line = TaxLine()
            tax_line.Amount = entry['TaxAmount']
            tax_line.DetailType = "TaxLineDetail"

            tax_line_detail = TaxLineDetail()
            tax_line_detail.TaxRateRef = Ref()
            tax_line_detail.TaxRateRef.value = entry['TaxRateRef']
            tax_line_detail.PercentBased = True
            tax_line_detail.TaxPercent = entry['TaxPercent']
            tax_line_detail.NetAmountTaxable = entry['NetAmountTaxable']

            tax_line.TaxLineDetail = tax_line_detail
            txn_tax_detail.TaxLine.append(tax_line)

        qb_invoice.TxnTaxDetail = txn_tax_detail
        qb_invoice.save(qb=self.api)

        return qb_invoice

    def serialize_response(self, response):
        """
        Serializes the response from QuickBooks to store the remote instance.
        """
        return response.to_ref()


    def set_remote_id(self, responsde_data):
        self.remote_instance.remote_id = responsde_data.value
