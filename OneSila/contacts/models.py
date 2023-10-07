from core import models
from django_shared_multi_tenant.validators import phone_regex

from .managers import SupplierManager, CustomerManager, InfluencerManager, \
    InvoiceAddressManager, ShippingAddressManager, InternalCompanyManager, \
    CompanyManager


class Company(models.Model):
    """
    An Company is essentially customer, supplier, influencers, any of the above.
    And sometimes they relate to each other for whatever reason like various branches or departments.
    """
    name = models.CharField(max_length=100)
    vat_number = models.CharField(max_length=100, blank=True, null=True)
    eori_number = models.CharField(max_length=100, blank=True, null=True)

    related_companies = models.ManyToManyField('self', symmetrical=True)

    is_supplier = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_influencer = models.BooleanField(default=False)
    is_internal_company = models.BooleanField(default=False)

    objects = CompanyManager()
    suppliers = SupplierManager()
    customers = CustomerManager()
    influencers = InfluencerManager()
    internal_companies = InternalCompanyManager()

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ("name", "multi_tenant_company")


class Supplier(Company):
    """
    A supplier is a contact, filtered as a proxy-model
    """
    objects = SupplierManager()

    class Meta:
        proxy = True


class Customer(Company):
    """
    A Customer is a contact, filtered as a proxy-model
    """
    objects = CustomerManager()

    class Meta:
        proxy = True


class Influencer(Company):
    """
    A Influencer is a contact, filtered as a proxy-model
    """
    objects = InfluencerManager()

    class Meta:
        proxy = True


class InternalCompany(Company):
    """
    Your own invoicing addresses, used for purchasing and selling
    """

    # TODO: When a new 'MultiTenantCompany' is created and completed. This model should be created
    # with that information as well.
    objects = InternalCompanyManager()

    class Meta:
        proxy = True


class Person(models.Model):
    """
    A person is someone attached to a contact.
    """
    from .languages import CUSTOMER_LANGUAGE_CHOICES

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)

    phone = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    language = models.CharField(max_length=2, default='EN', choices=CUSTOMER_LANGUAGE_CHOICES)

    def name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.name()


class Address(models.Model):
    """
    An address to be used by entities
    """
    from django_shared_multi_tenant.countries import COUNTRY_CHOICES

    contact = models.ForeignKey(Person, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    address1 = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100, blank=True, null=True)
    address3 = models.CharField(max_length=100, blank=True, null=True)

    postcode = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES)

    is_invoice_address = models.BooleanField(default=False)
    is_shipping_address = models.BooleanField(default=False)


class ShippingAddress(Address):
    objects = ShippingAddressManager()

    class Meta:
        proxy = True


class InvoiceAddress(Address):
    objects = InvoiceAddressManager()

    class Meta:
        proxy = True
