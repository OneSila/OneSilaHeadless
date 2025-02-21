from django.core.exceptions import ValidationError
from django.db.models import Q, Value
from django.utils.text import slugify

from core import models
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from translations.models import TranslationFieldsMixin, TranslatedModelMixin
from taxes.models import VatRate
from .managers import ProductManager, ConfigurableManager, BundleManager, VariationManager
import shortuuid
from hashlib import shake_256

import logging
logger = logging.getLogger(__name__)


class Product(TranslatedModelMixin, models.Model):
    from products.product_types import CONFIGURABLE, BUNDLE, SIMPLE,  PRODUCT_TYPE_CHOICES, HAS_PRICES_TYPES

    # Mandatory
    sku = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    active = models.BooleanField(default=True)
    type = models.CharField(max_length=15, choices=PRODUCT_TYPE_CHOICES)

    vat_rate = models.ForeignKey(VatRate, on_delete=models.PROTECT, null=True, blank=True)

    # for simple and dropshipping products, meaning allow product to be sold even when no physical stock is present.
    allow_backorder = models.BooleanField(default=False)

    configurable_variations = models.ManyToManyField('self',
        through='ConfigurableVariation',
        symmetrical=False,
        blank=True,
        related_name='configurables')

    bundle_variations = models.ManyToManyField('self',
        through='BundleVariation',
        symmetrical=False,
        blank=True,
        related_name='bundles')

    objects = ProductManager()
    variations = VariationManager()
    bundles = BundleManager()
    configurables = ConfigurableManager()

    @property
    def name(self):
        return self._get_translated_value(field_name='name', related_name='translations', fallback='sku')

    @property
    def url_key(self):
        return self._get_translated_value(field_name='url_key', related_name='translations')

    @property
    def ean_code(self):
        from eancodes.models import EanCode
        """
        Returns the EAN code for the product instance.
        - If the product has a direct EAN code, return it.
        - If the product is a variation and inherits an EAN code, return the inherited code.
        - Return None if no EAN code is associated.
        """
        direct_ean = EanCode.objects.filter(product=self, already_used=False).first()
        if direct_ean:
            return direct_ean.ean_code

        inherited_ean = EanCode.objects.filter(inherit_to=self, already_used=False).first()
        if inherited_ean:
            return inherited_ean.ean_code

        return None

    def __str__(self):
        return f"{self.name} <{self.sku}>"

    def set_active(self):
        self.active = True
        self.save()

    def set_inactive(self):
        self.active = False
        self.save()

    def is_configurable(self):
        return self.type == self.CONFIGURABLE

    def is_not_configurable(self):
        return self.type != self.CONFIGURABLE

    def is_bundle(self):
        return self.type == self.BUNDLE

    def is_not_bundle(self):
        return self.type != self.BUNDLE

    def is_simple(self):
        return self.type == self.SIMPLE

    def is_not_variations(self):
        return self.type != self.SIMPLE

    def deflate_bundle(self):
        """Return all BundleVariation items"""

        logger.debug(f"Trying to deflate {self} with {self.type=}")

        if self.type not in [self.BUNDLE]:
            raise ValueError(f"This only works for bundle products.")

        all_variation_ids = []

        variations = BundleVariation.objects.filter(parent=self)
        all_variation_ids.extend(variations.values_list('id', flat=True))

        for variation in variations:
            if variation.variation.is_bundle():
                all_variation_ids.extend(variation.variation.deflate_bundle().values_list('id', flat=True))
            else:
                all_variation_ids.append(variation.id)

        return BundleVariation.objects.filter(id__in=all_variation_ids)

    def get_parent_products(self, ids_only=False):
        product_ids = set()
        product_ids.add(self.id)

        bundles = BundleVariation.objects.filter(variation_id__in=product_ids)
        for bv in bundles.iterator():
            product_ids.add(bv.parent.id)

            logging.debug(f"Is this a bundle? {bv.parent=}?  {bv.parent.is_bundle()}")

            if bv.parent.is_bundle():
                product_ids.update(bv.parent.get_parent_products(ids_only=True))

        if ids_only:
            return product_ids

        return Product.objects.filter(id__in=product_ids)

    def get_proxy_instance(self):
        if self.is_simple():
            return SimpleProduct.objects.get(pk=self.pk)
        elif self.is_bundle():
            return BundleProduct.objects.get(pk=self.pk)
        elif self.is_configurable():
            return ConfigurableProduct.objects.get(pk=self.pk)
        else:
            return self

    def get_product_rule(self):
        from properties.models import ProductPropertiesRule
        from django.core.exceptions import ObjectDoesNotExist

        try:
            product_type_value = self.productproperty_set.get(property__is_product_type=True)
            return ProductPropertiesRule.objects.get(product_type_id=product_type_value.value_select.id, multi_tenant_company=self.multi_tenant_company)
        except ObjectDoesNotExist:
            return None

    def get_configurator_properties(self, product_rule=None):
        from properties.models import ProductPropertiesRuleItem

        return ProductPropertiesRuleItem.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            property__is_public_information=True,
            rule=product_rule or self.get_product_rule(),
            type__in=[
                ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
                ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR
            ]
        ).select_related('property')

    def get_optional_in_configurator_properties(self, product_rule=None):
        from properties.models import ProductPropertiesRuleItem

        return ProductPropertiesRuleItem.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            property__is_public_information=True,
            rule=product_rule or self.get_product_rule(),
            type=ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR
        ).select_related('property')

    def get_required_properties(self, product_rule=None):
        from properties.models import ProductPropertiesRuleItem

        return ProductPropertiesRuleItem.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            property__is_public_information=True,
            rule=product_rule or self.get_product_rule(),
            type__in=[
                ProductPropertiesRuleItem.REQUIRED,
                ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR,
                ProductPropertiesRuleItem.OPTIONAL_IN_CONFIGURATOR
            ]
        ).select_related('property')

    def get_optional_properties(self, product_rule=None):
        from properties.models import ProductPropertiesRuleItem

        return ProductPropertiesRuleItem.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            property__is_public_information=True,
            rule=product_rule or self.get_product_rule(),
            type=ProductPropertiesRuleItem.OPTIONAL
        ).select_related('property')

    def get_required_and_optional_properties(self, product_rule=None):
        from properties.models import ProductPropertiesRuleItem

        return ProductPropertiesRuleItem.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            property__is_public_information=True,
            rule=product_rule or self.get_product_rule(),
        ).select_related('property')

    def get_unique_configurable_variations(self):
        from properties.models import ProductProperty
        from django.db.models import Prefetch

        duplicate_decide_property_ids = self.get_configurator_properties().values_list('property_id', flat=True)
        attributes_len = len(duplicate_decide_property_ids)
        if len(duplicate_decide_property_ids) == 0:
            return Product.objects.none()

        configurable_variations = self.configurable_variations.prefetch_related(
            Prefetch(
                'productproperty_set',
                queryset=ProductProperty.objects.filter(property_id__in=duplicate_decide_property_ids),
                to_attr="relevant_properties"
            )
        )

        seen_keys = set()
        unique_variations_ids = set()
        for variation in configurable_variations:
            key = tuple(sorted(getattr(prop, 'value_select_id', None) for prop in variation.relevant_properties))

            if key not in seen_keys or attributes_len != len(key):
                seen_keys.add(key)
                unique_variations_ids.add(variation.id)

        return Product.objects.filter(id__in=unique_variations_ids)

    def get_price_for_sales_channel(self, sales_channel):
        from datetime import date
        from sales_prices.models import SalesPrice, SalesPriceListItem
        from sales_channels.models.sales_channels import SalesChannelIntegrationPricelist

        today = date.today()

        # Step 1: Check for Periodic Pricelist
        periodic_pricelist = SalesChannelIntegrationPricelist.objects.filter(
            sales_channel=sales_channel,
            price_list__start_date__lte=today,
            price_list__end_date__gte=today
        ).first()

        if periodic_pricelist:
            # Check for a price list item for this product
            price_item = SalesPriceListItem.objects.filter(
                salespricelist=periodic_pricelist.price_list,
                product=self
            ).annotate_prices().first()

            if price_item:
                return price_item.price, price_item.discount

        # Step 2: Check for Non-Periodic Pricelist
        non_periodic_pricelist = SalesChannelIntegrationPricelist.objects.filter(
            sales_channel=sales_channel,
            price_list__start_date__isnull=True,
            price_list__end_date__isnull=True
        ).first()

        if non_periodic_pricelist:
            price_item = SalesPriceListItem.objects.filter(
                salespricelist=non_periodic_pricelist.price_list,
                product=self
            ).annotate_prices().first()

            if price_item:
                return price_item.price, price_item.discount

        # Step 3: Use Default Product Price
        sales_price = SalesPrice.objects.filter(product=self).first()

        if sales_price:
            # Handle Case 1: Both RRP and price are available (and not None)
            if sales_price.rrp is not None and sales_price.price is not None:
                return sales_price.rrp, sales_price.price
            # Handle Case 2: Only RRP is available (price is None)
            elif sales_price.rrp is not None and sales_price.price is None:
                return sales_price.rrp, None
            # Handle Case 3: Only price is available (rrp is None)
            elif sales_price.price is not None and sales_price.rrp is None:
                return sales_price.price, None

        # Fallback if no price information is available
        return None, None

    def get_configurable_variations(self, active_only=True):
        """
        Returns the variations (child products) of this configurable product.

        :param active_only: If True, returns only active variations.
        :return: QuerySet of variation products.
        """
        # Ensure that this product is a configurable product
        if self.type != self.CONFIGURABLE:
            return Product.objects.none()

        variations = Product.objects.filter(
            configurablevariation_through_variations__parent=self
        )

        # Apply the active filter directly in the query if needed
        if active_only:
            variations = variations.filter(active=True)

        return variations

    def _generate_sku(self, save=False):
        self.sku = shake_256(shortuuid.uuid().encode('utf-8')).hexdigest(7)

    def save(self, *args, **kwargs):
        if not self.sku:
            self._generate_sku()

        super().save(*args, **kwargs)

    class Meta:
        search_terms = ['sku', 'translations__name']
        unique_together = ('sku', 'multi_tenant_company')


class BundleProduct(Product):
    from products.product_types import BUNDLE

    objects = BundleManager()
    proxy_filter_fields = {'type': BUNDLE}

    class Meta:
        proxy = True
        search_terms = ['sku']


class ConfigurableProduct(Product):
    from .product_types import CONFIGURABLE

    objects = ConfigurableManager()
    proxy_filter_fields = {'type': CONFIGURABLE}

    class Meta:
        proxy = True
        search_terms = ['sku']


class SimpleProduct(Product):
    from products.product_types import SIMPLE

    objects = VariationManager()
    proxy_filter_fields = {'type': SIMPLE}

    class Meta:
        proxy = True
        search_terms = ['sku']


class ConfigurableVariation(models.Model):
    parent = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="configurablevariation_through_parents")
    variation = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="configurablevariation_through_variations")

    def save(self, *args, **kwargs):
        if self.parent.is_not_configurable():
            raise IntegrityError(_("parent needs to a product of type CONFIGURABLE. Not %s" % (self.parent.type)))

        if self.variation.is_configurable():
            raise IntegrityError(_("variation needs to a product of type BUNDLE or SIMPLE. Not %s" % (self.parent.type)))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.parent} x {self.variation}"

    class Meta:
        unique_together = ("parent", "variation")


class BundleVariation(models.Model):
    parent = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="bundlevariation_through_parents")
    variation = models.ForeignKey('Product', on_delete=models.CASCADE, related_name="bundlevariation_through_variations")
    quantity = models.FloatField(default=1)

    def __str__(self):
        return f"{self.parent} x {self.quantity} {self.variation}"

    def save(self, *args, **kwargs):
        if self.parent.is_not_bundle():
            raise IntegrityError(_("parent needs to a product of type BUNDLE. Not %s" % (self.parent.type)))

        if self.variation.is_configurable():
            raise IntegrityError(_("variation needs to a product of type BUNDLE or SIMPLE. Not %s" % (self.parent.type)))

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ("parent", "variation")


class ProductTranslation(TranslationFieldsMixin, models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="translations")

    name = models.CharField(max_length=100)
    short_description = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url_key = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.product} <{self.language}>"

    def _get_default_url_key(self):
        new_url_key = slugify(self.name)

        if ProductTranslation.objects.filter(url_key=new_url_key, multi_tenant_company=self.multi_tenant_company).exists():
            # sku is unique so this will solve everything
            new_url_key += f'-{self.product.sku}-{self.language}'

        return new_url_key

        return None

    def save(self, *args, **kwargs):
        if not self.url_key:
            self.url_key = self._get_default_url_key()

        super().save(*args, **kwargs)

    class Meta:
        translated_field = 'product'
        unique_together = (
            ('product', 'language'),
            ('url_key', 'multi_tenant_company'),
        )