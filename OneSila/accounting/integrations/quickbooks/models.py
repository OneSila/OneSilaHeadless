from accounting.models.remote_instance import AccountingMirrorAccount, AccountingMirrorInvoice, AccountingMirrorCreditNote, AccountingMirrorCustomer, AccountingMirrorVat
from core import models

class QuickbooksAccount(AccountingMirrorAccount):
    """
    QuickBooks-specific implementation of an AccountingMirrorAccount.
    Includes authentication fields and configuration options.
    """
    # Constants for environment choices
    SANDBOX = 'sandbox'
    PRODUCTION = 'production'

    ENVIRONMENT_CHOICES = (
        (SANDBOX, 'Sandbox'),
        (PRODUCTION, 'Production'),
    )

    # Authentication fields for QuickBooks
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    company_id = models.CharField(max_length=255)
    environment = models.CharField(max_length=50, choices=ENVIRONMENT_CHOICES)
    redirect_uri = models.URLField(blank=True, null=True)

    code_of_service = models.CharField(max_length=100, null=True, blank=True, help_text="Code of service for QuickBooks integration.")

    # OAuth fields
    authorization_code = models.CharField(max_length=512, blank=True, null=True, help_text="Authorization code for OAuth2.")
    realm_id = models.CharField(max_length=255, blank=True, null=True, help_text="QuickBooks realm ID.")

    # Token fields
    access_token = models.CharField(max_length=1024, blank=True, null=True)
    refresh_token = models.CharField(max_length=1024, blank=True, null=True)
    token_expiration = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'QuickBooks Account'
        verbose_name_plural = 'QuickBooks Accounts'

    def __str__(self):
        return f"QuickBooks Account for {self.internal_company}"


class QuickbooksInvoice(AccountingMirrorInvoice):
    """
    QuickBooks-specific implementation of a AccountingMirrorInvoice.
    """
    pass


class QuickbooksCreditNote(AccountingMirrorCreditNote):
    """
    QuickBooks-specific implementation of a AccountingMirrorCreditNote.
    """
    pass


class QuickbooksCustomer(AccountingMirrorCustomer):
    """
    QuickBooks-specific implementation of an AccountingMirrorCustomer.
    Stores remote_id and sync_token for synchronization.
    """
    pass

    class Meta:
        verbose_name = "QuickBooks Customer"
        verbose_name_plural = "QuickBooks Customers"


class QuickbooksVat(AccountingMirrorVat):
    remote_name = models.CharField(max_length=255, null=True, blank=True, help_text="Name of the tax code in QuickBooks")
    tax_rate_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID of the TaxRate in QuickBooks")
    tax_rate_name = models.CharField(max_length=255, null=True, blank=True, help_text="Name of the TaxRate in QuickBooks")
    rate_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Rate percentage of the TaxRate")

    def __str__(self):
        return f"QuickbooksVat(remote_name={self.remote_name}, local_instance={self.local_instance})"