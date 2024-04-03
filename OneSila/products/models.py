from core import models
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from core.models import MultiTenantAwareMixin
from translations.models import TranslationFieldsMixin
from taxes.models import VatRate

from .managers import ProductManger, UmbrellaManager, BundleManager, VariationManager


class Product(models.Model):
    VARIATION = 'VARIATION'
    BUNDLE = 'BUNDLE'
    UMBRELLA = 'UMBRELLA'

    PRODUCT_TYPE_CHOICES = (
        (VARIATION, _('Product Variation')),
        (BUNDLE, _('Bundle Product')),
        (UMBRELLA, _('Umbrella Product')),
    )

    sku = models.CharField(max_length=100, unique=True, db_index=True)
    active = models.BooleanField(default=False)
    type = models.CharField(max_length=9, choices=PRODUCT_TYPE_CHOICES)
    vat_rate = models.ForeignKey(VatRate, on_delete=models.PROTECT)
    always_on_stock = models.BooleanField(default=False)

    umbrella_variations = models.ManyToManyField('self',
        through='UmbrellaVariation',
        symmetrical=False,
        blank=True,
        related_name='umbrellas')

    bundle_variations = models.ManyToManyField('self',
        through='BundleVariation',
        symmetrical=False,
        blank=True,
        related_name='bundles')

    objects = ProductManger()
    variations = VariationManager()
    bundles = BundleManager()
    umbrellas = UmbrellaManager()

    def __str__(self):
        return f"{self.sku}"

    def set_active(self):
        self.active = True
        self.save()

    def set_inactive(self):
        self.active = False
        self.save()

    def is_umbrella(self):
        return self.type == self.UMBRELLA

    def is_not_umbrella(self):
        return self.type != self.UMBRELLA

    def is_bundle(self):
        return self.type == self.BUNDLE

    def is_not_bundle(self):
        return self.type != self.BUNDLE

    def is_variation(self):
        return self.type == self.VARIATION

    def is_not_variations(self):
        return self.type != self.VARIATION

    def get_proxy_instance(self):
        if self.is_variation():
            return ProductVariation.objects.get(pk=self.pk)
        elif self.is_bundle():
            return BundleProduct.objects.get(pk=self.pk)
        elif self.is_umbrella():
            return UmbrellaProduct.objects.get(pk=self.pk)
        else:
            return self

    class Meta:
        search_terms = ['sku']


class BundleProduct(Product):
    objects = BundleManager()

    class Meta:
        proxy = True


class UmbrellaProduct(Product):
    objects = UmbrellaManager()

    class Meta:
        proxy = True


class ProductVariation(Product):
    objects = VariationManager()

    class Meta:
        proxy = True


class ProductTranslation(TranslationFieldsMixin, models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="translations")

    name = models.CharField(max_length=100)
    short_description = models.TextField()
    description = models.TextField()
    url_key = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.product} <{self.language}>"

    class Meta:
        unique_together = ('product', 'language')


class UmbrellaVariation(models.Model):
    umbrella = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="umbrellavariation_umbrellas")
    variation = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="umbrellavariation_variations")

    def save(self, *args, **kwargs):
        if self.umbrella.is_not_umbrella():
            raise IntegrityError(_("umbrella needs to a product of type UMBRELLA. Not %s" % (self.umbrella.type)))

        if self.variation.is_umbrella():
            raise IntegrityError(_("variation needs to a product of type BUNDLE or VARIATION. Not %s" % (self.umbrella.type)))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.umbrella} x {self.variation}"

    class Meta:
        unique_together = ("umbrella", "variation")


class BundleVariation(models.Model):
    umbrella = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="bundlevariation_umbrellas")
    variation = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="bundlevariation_variations")
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.umbrella} x {self.quantity} {self.variation}"

    def save(self, *args, **kwargs):
        if self.umbrella.is_not_bundle():
            raise IntegrityError(_("umbrella needs to a product of type BUNDLE. Not %s" % (self.umbrella.type)))

        if self.variation.is_umbrella():
            raise IntegrityError(_("variation needs to a product of type BUNDLE or VARIATION. Not %s" % (self.umbrella.type)))

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("umbrella", "variation")
