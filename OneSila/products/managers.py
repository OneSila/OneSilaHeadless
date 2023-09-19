from django.db.models import QuerySet, Manager


class ProductQuerySet(QuerySet):
    def filter_umbrella(self):
        return self.filter(type=self.model.UMBRELLA)

    def filter_variation(self):
        return self.filter(type=self.model.VARIATION)

    def filter_bundle(self):
        return self.filter(type=self.model.BUNDLE)


class ProductManger(Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)


class UmbrellaManager(ProductManger):
    def get_queryset(self):
        return super().get_queryset().filter_umbrella()

    def create(self, *args, **kwargs):
        return super().create(type=self.model.UMBRELLA, **kwargs)


class VariationManager(ProductManger):
    def get_queryset(self):
        return super().get_queryset().filter_variation()

    def create(self, *args, **kwargs):
        return super().create(type=self.model.VARIATION, **kwargs)


class BundleManager(ProductManger):
    def get_queryset(self):
        return super().get_queryset().filter_bundle()

    def create(self, *args, **kwargs):
        return super().create(type=self.model.BUNDLE, **kwargs)
