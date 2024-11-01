from quickbooks.objects import CreditMemo, SalesItemLine, Ref, SalesItemLineDetail, EmailAddress, TxnTaxDetail, TaxLine, TaxLineDetail
from accounting.factories.remote_instance.remote_instance import RemoteCreditNoteCreateFactory
from accounting.integrations.quickbooks.factories import GetQuickbooksAPIMixin, GetOrCreateQuickbooksCustomerMixin, GetCreateOrUpdateItemMixin
from accounting.integrations.quickbooks.models import QuickbooksCreditMemo, QuickbooksVat

class QuickbooksCreditMemoCreateFactory(GetQuickbooksAPIMixin, GetOrCreateQuickbooksCustomerMixin, GetCreateOrUpdateItemMixin, RemoteCreditNoteCreateFactory):
    remote_model_class = QuickbooksCreditMemo  # You'll need to create this model similar to QuickbooksInvoice

    field_mapping = {
        'document_number': 'DocNumber',
    }

    def __init__(self, remote_account, local_instance, api=None):
        self.customer = local_instance.order_return.customer
        self.order_return = local_instance.order_return

        super().__init__(remote_account, local_instance, api)

    def get_remote_vat(self, product):
        # Same as in your invoice factory
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
        Custom logic to create a credit memo in QuickBooks using the SDK.
        Includes handling line items and tax details.
        """
        qb_credit_memo = CreditMemo()

        for local_field, remote_field in self.field_mapping.items():
            setattr(qb_credit_memo, remote_field, getattr(self.local_instance, local_field, None))

        qb_credit_memo.CustomerRef = self.get_quickbooks_customer().to_ref()

        if self.local_instance.document_date:
            qb_credit_memo.TxnDate = self.local_instance.document_date.strftime('%Y-%m-%d')

        if self.local_instance.price_incl_vat:
            qb_credit_memo.GlobalTaxCalculation = "TaxInclusive"
        else:
            qb_credit_memo.GlobalTaxCalculation = "TaxExcluded"

        if self.order_return.sales_channel.shipping_address:
            qb_credit_memo.BillAddr = self.map_address(self.order_return.sales_channel.invoice_address)

        if self.order_return.sales_channel.shipping_address:
            qb_credit_memo.ShipAddr = self.map_address(self.order_return.sales_channel.shipping_address)

        if self.customer.email:
            qb_credit_memo.BillEmail = EmailAddress()
            qb_credit_memo.BillEmail.Address = self.customer.email

        line_num_counter = 1
        total_tax = 0.0
        tax_summary = {}

        for line_item in self.local_instance.items.all():
            qb_line = SalesItemLine()
            qb_line.DetailType = "SalesItemLineDetail"
            qb_line.Description = line_item.name
            qb_line.Amount = float(line_item.line_total) * -1
            qb_line.LineNum = line_num_counter

            item = self.get_or_create_item(line_item, line_item.order_return_item.product)
            detail = SalesItemLineDetail()
            detail.ItemRef = item.to_ref()
            detail.Qty = line_item.quantity
            detail.UnitPrice = float(line_item.unit_price)

            product = line_item.order_return_item.product
            local_vat = product.vat_rate

            try:
                remote_vat = self.get_remote_vat(product)
            except Exception as e:
                raise Exception(f"Tax code not found for product {product}: {e}")

            tax_code_ref = Ref()
            tax_code_ref.value = remote_vat.tax_code_id
            detail.TaxCodeRef = tax_code_ref

            qb_line.SalesItemLineDetail = detail
            qb_credit_memo.Line.append(qb_line)

            vat_percentage = float(remote_vat.rate_value)
            line_amount = float(line_item.line_total) * -1

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

        qb_credit_memo.TxnTaxDetail = txn_tax_detail
        qb_credit_memo.save(qb=self.api)

        return qb_credit_memo

    def serialize_response(self, response):
        """
        Serializes the response from QuickBooks to store the remote instance.
        """
        return response.to_ref()

    def set_remote_id(self, response_data):
        self.remote_instance.remote_id = response_data.value
