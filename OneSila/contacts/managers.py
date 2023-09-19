from django.db.models import QuerySet, Manager


class EntityQueryset(QuerySet):
    def filter_supplier(self):
        return self.filter(is_supplier=True)

    def filter_customer(self):
        return self.filter(is_customer=True)

    def filter_influencer(self):
        return self.filter(is_influencer=True)


class SupplierManager(Manager):
    def get_queryset(self):
        return EntityQueryset(self.model, using=self._db).\
            filter_supplier()

    def create(self, *args, **kwargs):
        return super().create(is_supplier=True, **kwargs)


class CustomerManager(Manager):
    def get_queryset(self):
        return EntityQueryset(self.model, using=self._db).\
            filter_customer()

    def create(self, *args, **kwargs):
        return super().create(is_customer=True, **kwargs)


class InfluencerManager(Manager):
    def get_queryset(self):
        return EntityQueryset(self.model, using=self._db).\
            filter_influencer()

    def create(self, *args, **kwargs):
        return super().create(is_influencer=True, **kwargs)


class InternalCompanyManager(Manager):
    def get_queryset(self):
        return EntityQueryset(self.model, using=self._db).\
            filter_internal_company()

    def create(self, *args, **kwargs):
        return super() > create(is_internal_company=True, **kwargs)


class AddressQuerySet(QuerySet):
    def filter_shippingaddress(self):
        return self.filter(is_shippingaddress=True)

    def filter_invoiceaddress(self):
        return self.filter(is_invoiceaddress=True)


class ShippingAddressManager(Manager):
    def get_queryset(self):
        return AddressQuerySet(self.model, using=self._db).\
            filter_shippingaddress()


class InvoiceAddressManager(Manager):
    def get_queryset(self):
        return AddressQuerySet(self.model, using=self._db).\
            filter_invoiceaddress()
