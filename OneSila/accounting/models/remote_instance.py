from polymorphic.models import PolymorphicModel
from accounting.models.mixins import RemoteObjectMixin
from core import models
from integrations.models import Integration


class AccountingMirrorAccount(Integration):
    """
    AccountingMirror of an accounting account. Inherits from Integration.
    """
    due_days = models.IntegerField(null=True, blank=True, help_text="The number of days before payment is due.")
    invoice_layout = models.FileField(null=True, blank=True, upload_to='invoices/', help_text="The invoice layout PDF.")

    class Meta:
        verbose_name = 'AccountingMirror Account'
        verbose_name_plural = 'AccountingMirror Accounts'

    def __str__(self):
        return f"AccountingMirror Account for {self.internal_company}"

class AccountingMirrorInvoice(PolymorphicModel, RemoteObjectMixin):
    """
    AccountingMirror of an Invoice. Inherits common fields from RemoteObjectMixin.
    """
    local_instance = models.ForeignKey('accounting.Invoice', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'AccountingMirror Invoice'
        verbose_name_plural = 'AccountingMirror Invoices'

    def __str__(self):
        return f"AccountingMirror Invoice for {self.local_instance}"


class AccountingMirrorCreditNote(PolymorphicModel, RemoteObjectMixin):
    """
    AccountingMirror of a Credit Note. Inherits common fields from RemoteObjectMixin.
    """
    local_instance = models.ForeignKey('accounting.CreditNote', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'AccountingMirror Credit Note'
        verbose_name_plural = 'AccountingMirror Credit Notes'

    def __str__(self):
        return f"AccountingMirror Credit Note for {self.local_instance}"

class AccountingMirrorCustomer(PolymorphicModel, RemoteObjectMixin):
    """
    AccountingMirror of a Customer.
    """
    local_instance = models.ForeignKey('contacts.Company', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'AccountingMirror Customer'
        verbose_name_plural = 'AccountingMirror Customers'

    def __str__(self):
        return f"AccountingMirror Customer {self.local_instance}"

class AccountingMirrorVat(PolymorphicModel, RemoteObjectMixin):
    """
    AccountingMirror of VAT rates or tax settings.
    """
    local_instance = models.ForeignKey('taxes.VatRate', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'AccountingMirror VAT'
        verbose_name_plural = 'AccountingMirror VATs'

    def __str__(self):
        return f"AccountingMirror VAT {self.local_instance}"