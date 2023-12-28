from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin, \
    QuerySetProxyModelMixin


class CompanyQueryset(MultiTenantCompanyCreateMixin, QuerySet):
    search_terms = ['name']

    def filter_supplier(self):
        return self.filter(is_supplier=True)

    def filter_customer(self):
        return self.filter(is_customer=True)

    def filter_influencer(self):
        return self.filter(is_influencer=True)


class CompanyManager(MultiTenantCompanyCreateMixin, Manager):
    def get_queryset(self):
        return CompanyQueryset(self.model, using=self._db)


class SupplierQuerySet(QuerySetProxyModelMixin, CompanyQueryset):
    pass


class SupplierManager(CompanyManager):
    def get_queryset(self):
        return SupplierQuerySet(self.model, using=self._db)


class CustomerQuerySet(QuerySetProxyModelMixin, CompanyQueryset):
    pass


class CustomerManager(CompanyManager):
    def get_queryset(self):
        return CustomerQuerySet(self.model, using=self._db)


class InfluencerQuerySet(QuerySetProxyModelMixin, CompanyQueryset):
    pass


class InfluencerManager(CompanyManager):
    def get_queryset(self):
        return InfluencerQuerySet(self.model, using=self._db)


class InternalCompanyQuerySet(QuerySetProxyModelMixin, CompanyQueryset):
    pass


class InternalCompanyManager(CompanyManager):
    def get_queryset(self):
        return InternalCompany(self.model, using=self._db)


class AddressQuerySet(MultiTenantCompanyCreateMixin, QuerySet):
    def filter_shippingaddress(self):
        return self.filter(is_shipping_address=True)

    def filter_invoiceaddress(self):
        return self.filter(is_invoice_address=True)


class ShippingAddressQuerySet(QuerySetProxyModelMixin, AddressQuerySet):
    pass


class ShippingAddressManager(Manager):
    def get_queryset(self):
        return ShippingAddressQuerySet(self.model, using=self._db)


class InvoiceAddressQuerySet(QuerySetProxyModelMixin, AddressQuerySet):
    pass


class InvoiceAddressManager(Manager):
    def get_queryset(self):
        return InvoiceAddressQuerySet(self.model, using=self._db)
