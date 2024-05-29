from core import models
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from translations.models import TranslationFieldsMixin
from taxes.models import VatRate
from .managers import ProductManger, UmbrellaManager, BundleManager, VariationManager
import shortuuid
from hashlib import shake_256


class Product(models.Model):
    from products.product_types import UMBRELLA, VARIATION, BUNDLE, PRODUCT_TYPE_CHOICES

    sku = models.CharField(max_length=100, db_index=True, blank=True, null=True)
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

    @property
    def name(self):
        translations = self.translations.all()
        lang = self.multi_tenant_company.language
        name = self.sku

        if translations:
            try:
                translation = translations.get(language=lang)
            except ProductTranslation.DoesNotExist:
                translation = translations.last()

            name = translation.name

        return f"{name}"
    def __str__(self):
        return f"{self.name}"

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

    def _generate_sku(self, save=False):
        self.sku = shake_256(shortuuid.uuid().encode('utf-8')).hexdigest(7)

    def save(self, *args, **kwargs):
        if not self.sku:
            self._generate_sku()

        super().save(*args, **kwargs)

    class Meta:
        search_terms = ['sku', 'translations__name']
        unique_together = ("sku", "multi_tenant_company")


class BundleProduct(Product):
    from products.product_types import BUNDLE

    objects = BundleManager()
    proxy_filter_fields = {'type': BUNDLE}

    class Meta:
        proxy = True
        search_terms = ['sku']


class UmbrellaProduct(Product):
    from .product_types import UMBRELLA

    objects = UmbrellaManager()
    proxy_filter_fields = {'type': UMBRELLA}

    class Meta:
        proxy = True
        search_terms = ['sku']


class ProductVariation(Product):
    from products.product_types import VARIATION

    objects = VariationManager()
    proxy_filter_fields = {'type': VARIATION}

    class Meta:
        proxy = True
        search_terms = ['sku']


class ProductTranslation(TranslationFieldsMixin, models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="translations")

    name = models.CharField(max_length=100)
    short_description = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
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
