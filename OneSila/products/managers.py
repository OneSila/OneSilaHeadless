from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin, \
    QuerySetProxyModelMixin, MultiTenantQuerySet, MultiTenantManager


class ProductQuerySet(MultiTenantQuerySet):
    def filter_umbrella(self):
        return self.filter(type=self.model.UMBRELLA)

    def filter_variation(self):
        return self.filter(type=self.model.SIMPLE)

    def filter_bundle(self):
        return self.filter(type=self.model.BUNDLE)

    def filter_manufacturer(self):
        return self.filter(type=self.model.MANUFACTURER)

    def filter_dropship(self):
        return self.filter(type=self.model.DROPSHIP)

    def filter_has_prices(self):
        return self.filter(type__in=self.model.HAS_PRICES_TYPES)


class ProductManager(MultiTenantManager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)


class UmbrellaQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class UmbrellaManager():
    def get_queryset(self):
        return UmbrellaQuerySet(self.model, using=self._db)


class VariationQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class VariationManager(ProductManager):
    def get_queryset(self):
        return VariationQuerySet(self.model, using=self._db)


class BundleQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class BundleManager(ProductManager):
    def get_queryset(self):
        return BundleQuerySet(self.model, using=self._db)


class ManufacturableQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class ManufacturableManager(ProductManager):
    def get_queryset(self):
        return ManufacturableQuerySet(self.model, using=self._db)


class DropshipQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class DropshipManager(ProductManager):
    def get_queryset(self):
        return DropshipQuerySet(self.model, using=self._db)


class SupplierProductQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class SupplierProductManager(ProductManager):
    def get_queryset(self):
        return SupplierProductQuerySet(self.model, using=self._db)
