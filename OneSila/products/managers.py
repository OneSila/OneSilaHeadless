from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin, \
    QuerySetProxyModelMixin, MultiTenantQuerySet, MultiTenantManager


class ProductQuerySet(MultiTenantQuerySet):
    def filter_umbrella(self):
        return self.filter(type=self.model.UMBRELLA)

    def filter_variation(self):
        return self.filter(type=self.model.VARIATION)

    def filter_bundle(self):
        return self.filter(type=self.model.BUNDLE)


class ProductManger(MultiTenantManager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)


class UmbrellaQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class UmbrellaManager():
    def get_queryset(self):
        return UmbrellaQuerySet(self.model, using=self._db)


class VariationQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class VariationManager(ProductManger):
    def get_queryset(self):
        return VariationQuerySet(self.model, using=self._db)


class BundleQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class BundleManager(ProductManger):
    def get_queryset(self):
        return BundleQuerySet(self.model, using=self._db)
