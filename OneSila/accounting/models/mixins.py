from decimal import Decimal
from core import models
from integrations.models import IntegrationObjectMixin


class DocumentBase(models.Model):
    # 1. Document Identification
    document_number = models.CharField(max_length=100)
    document_date = models.DateField()
    order_number = models.CharField(max_length=100, blank=True, null=True)

    # 2. Parties Involved (preserved fields)
    # Vendor Details
    vendor_name = models.CharField(max_length=255)
    vendor_address = models.TextField()
    vendor_email = models.EmailField(blank=True, null=True)
    vendor_phone = models.CharField(max_length=20, blank=True, null=True)

    # Customer Details
    customer_name = models.CharField(max_length=255)
    customer_invoice_address = models.TextField()
    customer_shipping_address = models.TextField(blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    # VAT Details
    vendor_vat_number = models.CharField(max_length=50, blank=True, null=True)
    customer_vat_number = models.CharField(max_length=50, blank=True, null=True)

    # 4. Financials
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # is null because we calculate after create
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency_symbol = models.CharField(max_length=20)
    price_incl_vat = models.BooleanField(default=True)

    class Meta:
        abstract = True
        unique_together = ("document_number", "multi_tenant_company")

class DocumentItemBase(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.ForeignKey('taxes.VatRate', on_delete=models.SET_NULL, null=True)
    preserved_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    class Meta:
        abstract = True

    @property
    def line_total(self):
        """
        Calculate the total for this line item (quantity * unit price).
        """
        return Decimal(self.quantity * self.unit_price)


class RemoteObjectMixin(IntegrationObjectMixin):
    """
    Mixin for objects that are tied to a specific sales_channel integration.
    """
    remote_account = models.ForeignKey('accounting.AccountingMirrorAccount', on_delete=models.CASCADE, db_index=True)

    @property
    def integration(self):
        """
        Returns the remote_account as the integration.
        """
        return self.remote_account

    class Meta:
        abstract = True
