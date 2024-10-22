from accounting.factories.remote_instance.mixins import AccountingRemoteInstanceCreateFactory
from accounting.models import Invoice, CreditNote
from taxes.models import VatRate


class RemoteInvoiceCreateFactory(AccountingRemoteInstanceCreateFactory):
    local_model_class = Invoice

class RemoteCreditNoteCreateFactory(AccountingRemoteInstanceCreateFactory):
    local_model_class = CreditNote

class RemoteVatCreateFactory(AccountingRemoteInstanceCreateFactory):
    local_model_class = VatRate
