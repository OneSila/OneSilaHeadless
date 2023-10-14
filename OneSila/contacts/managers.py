from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin


class QuerySetFilterCreateOverride:
    def filter(self, *args, **kwargs):
        kwargs.update(self.model.filter_create_overrides)
        return super().filter(*args, **kwargs)

    def create(self, **kwargs):
        kwargs.update(self.model.filter_create_overrides)
        return super().create(**kwargs)

    def all(self):
        return self.filter()


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


class SupplierQuerySet(QuerySetFilterCreateOverride, MultiTenantCompanyCreateMixin, QuerySet):
    pass


class SupplierManager(CompanyManager):
    def get_queryset(self):
        return SupplierQuerySet(self.model, using=self._db)


class CustomerQuerySet(QuerySetFilterCreateOverride, MultiTenantCompanyCreateMixin, QuerySet):
    pass


class CustomerManager(CompanyManager):
    def get_queryset(self):
        return CustomerQuerySet(self.model, using=self._db)


class InfluencerQuerySet(QuerySetFilterCreateOverride, MultiTenantCompanyCreateMixin, QuerySet):
    pass


class InfluencerManager(CompanyManager):
    def get_queryset(self):
        return InfluencerQuerySet(self.model, using=self._db)


class InternalCompanyQuerySet(QuerySetFilterCreateOverride, MultiTenantCompanyCreateMixin, QuerySet):
    pass


class InternalCompanyManager(CompanyManager):
    def get_queryset(self):
        return InternalCompany(self.model, using=self._db)


class AddressQuerySet(MultiTenantCompanyCreateMixin, QuerySet):
    def filter_shippingaddress(self):
        return self.filter(is_shipping_address=True)

    def filter_invoiceaddress(self):
        return self.filter(is_invoice_address=True)


class ShippingAddressQuerySet(QuerySetFilterCreateOverride, MultiTenantCompanyCreateMixin, QuerySet):
    pass


class ShippingAddressManager(Manager):
    def get_queryset(self):
        return ShippingAddressQuerySet(self.model, using=self._db)


class InvoiceAddressQuerySet(QuerySetFilterCreateOverride, MultiTenantCompanyCreateMixin, QuerySet):
    pass


class InvoiceAddressManager(Manager):
    def get_queryset(self):
        return InvoiceAddressQuerySet(self.model, using=self._db)
