from quickbooks.objects import TaxRate, TaxCode

from accounting.integrations.quickbooks.factories import GetQuickbooksAPIMixin
from accounting.integrations.quickbooks.models import QuickbooksVat


class QuickbooksVatPullFactory(GetQuickbooksAPIMixin):

    def __init__(self, remote_account, api=None):
        self.remote_account = remote_account
        self.api = api or self.get_api()
        self.multi_tenant_company =self.remote_account.multi_tenant_company


    def sync_tax_codes(self):
        """
        Fetches all tax codes and their associated tax rates from QuickBooks.
        Creates/updates QuickbooksVat instances for each tax rate within a tax code.
        """
        tax_codes = TaxCode.all(qb=self.api)

        for tax_code in tax_codes:
            tax_code_id = tax_code.Id
            tax_code_name = tax_code.Name
            is_tax_group = getattr(tax_code, 'TaxGroup', False)
            sales_tax_rate_list = tax_code.SalesTaxRateList

            if sales_tax_rate_list and sales_tax_rate_list.TaxRateDetail:
                tax_rate_details = sales_tax_rate_list.TaxRateDetail

                for tax_rate_detail in tax_rate_details:
                    tax_rate_ref = tax_rate_detail.TaxRateRef.value
                    tax_rate = TaxRate.get(tax_rate_ref, qb=self.api)

                    vat_instance, created = QuickbooksVat.objects.get_or_create(
                        remote_account=self.remote_account,
                        multi_tenant_company=self.multi_tenant_company,
                        remote_id=tax_code_id,
                        tax_rate_id=tax_rate.Id,
                    )

                    if created:
                        vat_instance.remote_name = tax_code_name
                        vat_instance.tax_rate_name = tax_rate.Name
                        vat_instance.rate_value = tax_rate.RateValue
                        vat_instance.save()
                    else:
                        updated = False
                        if vat_instance.remote_name != tax_code_name:
                            vat_instance.remote_name = tax_code_name
                            updated = True
                        if vat_instance.tax_rate_name != tax_rate.Name:
                            vat_instance.tax_rate_name = tax_rate.Name
                            updated = True
                        if vat_instance.rate_value != tax_rate.RateValue:
                            vat_instance.rate_value = tax_rate.RateValue
                            updated = True
                        if updated:
                            vat_instance.save()

    def run(self):
        self.sync_tax_codes()