from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin


class CompanyQueryset(QuerySet):
    def filter_supplier(self):
        return self.filter(is_supplier=True)

    def filter_customer(self):
        return self.filter(is_customer=True)

    def filter_influencer(self):
        return self.filter(is_influencer=True)


class CompanyManager(MultiTenantCompanyCreateMixin, Manager):
    def get_queryset(self):
        return CompanyQueryset(self.model, using=self._db)


class SupplierManager(CompanyManager):
    def get_queryset(self):
        return CompanyQueryset(self.model, using=self._db).\
            filter_supplier()

    def create(self, **kwargs):
        # What if is_supplier is already set?  Hard override.
        kwargs.update({'is_supplier': True})
        return super().create(**kwargs)


class CustomerManager(CompanyManager):
    def get_queryset(self):
        return CompanyQueryset(self.model, using=self._db).\
            filter_customer()

    def create(self, **kwargs):
        kwargs.update({'is_customer': True})
        return super().create(**kwargs)


class InfluencerManager(CompanyManager):
    def get_queryset(self):
        return CompanyQueryset(self.model, using=self._db).\
            filter_influencer()

    def create(self, **kwargs):
        kwargs.update({'is_influencer': True})
        return super().create(**kwargs)


class InternalCompanyManager(CompanyManager):
    def get_queryset(self):
        return CompanyQueryset(self.model, using=self._db).\
            filter_internal_company()

    def create(self, **kwargs):
        kwargs.update({'is_internal_company': True})
        return super().create(**kwargs)


class AddressQuerySet(MultiTenantCompanyCreateMixin, QuerySet):
    def filter_shippingaddress(self):
        return self.filter(is_shipping_address=True)

    def filter_invoiceaddress(self):
        return self.filter(is_invoice_address=True)


class ShippingAddressManager(MultiTenantCompanyCreateMixin, Manager):
    def get_queryset(self):
        return AddressQuerySet(self.model, using=self._db).\
            filter_shippingaddress()


class InvoiceAddressManager(MultiTenantCompanyCreateMixin, Manager):
    def get_queryset(self):
        return AddressQuerySet(self.model, using=self._db).\
            filter_invoiceaddress()
