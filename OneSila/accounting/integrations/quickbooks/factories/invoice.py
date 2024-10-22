from quickbooks.objects import Invoice, SalesItemLine, Ref, SalesItemLineDetail, Account, TaxCode, EmailAddress

from accounting.factories.remote_instance.remote_instance import RemoteInvoiceCreateFactory
from accounting.integrations.quickbooks.factories import GetQuickbooksAPIMixin, GetOrCreateQuickbooksCustomerMixin, GetCreateOrUpdateItemMixin
from accounting.integrations.quickbooks.models import QuickbooksInvoice


class QuickbooksInvoiceCreateFactory(GetQuickbooksAPIMixin, GetOrCreateQuickbooksCustomerMixin, GetCreateOrUpdateItemMixin, RemoteInvoiceCreateFactory):
    remote_model_class = QuickbooksInvoice

    field_mapping = {
        'document_number': 'DocNumber',
    }

    def __init__(self, remote_account, local_instance, api=None):
        self.customer = local_instance.sales_order.customer
        self.sales_order = local_instance.sales_order

        super().__init__(remote_account, local_instance, api)

    def create_remote(self):
        """
        Custom logic to create an invoice in QuickBooks using the SDK.
        Includes handling line items.
        """
        qb_invoice = Invoice()

        for local_field, remote_field in self.field_mapping.items():
            setattr(qb_invoice, remote_field, getattr(self.local_instance, local_field, None))

        # qb_invoice.TotalAmt = float(self.local_instance.total) This is readonly calculated by the system
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
        for line_item in self.local_instance.items.all():
            qb_line = SalesItemLine()
            qb_line.DetailType = "SalesItemLineDetail"
            qb_line.Description = line_item.name
            qb_line.Amount = float(line_item.line_total)
            qb_line.LineNum = line_num_counter

            item = self.get_or_create_item(line_item, line_item.order_item.product)
            detail =  SalesItemLineDetail()
            detail.ItemRef = item.to_ref()
            detail.Qty = line_item.quantity
            detail.UnitPrice = float(line_item.unit_price)

            qb_line.SalesItemLineDetail = detail

            if tax_code_ref is not None:
                qb_line.SalesItemLineDetail.TaxCodeRef = tax_code_ref


            line_num_counter += 1
            qb_invoice.Line.append(qb_line)

        qb_invoice.save(qb=self.api)

        return qb_invoice

    def serialize_response(self, response):
        """
        Serializes the response from QuickBooks to store the remote instance.
        """
        return response.to_ref()


    def set_remote_id(self, responsde_data):
        self.remote_instance.remote_id = responsde_data.value