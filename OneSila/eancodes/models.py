from core import models
from django.db import IntegrityError
from products.models import Product, SupplierProduct
from django.utils.translation import gettext_lazy as _

import logging
logger = logging.getLogger(__name__)


class EanCode(models.Model):
    """
    Ean-codes are designed to be kept track of, for whoever buys their own codes.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ean_code = models.CharField(max_length=14, blank=True, null=True)
    inherit_to = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inherited_ean_codes'
    )
    internal = models.BooleanField(default=True, help_text='Generated from the prefix')
    already_used = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.ean_code)

    @property
    def product_name(self):
        if self.product:
            return self.product.name

        if self.inherit_to:
            return self.inherit_to.name

        return None

    def clean(self):
        if not self.ean_code and not self.inherit_to:
            raise IntegrityError("Either Ean Code or Inherit To must be provided.")
        if self.product and self.product.is_umbrella():
            raise IntegrityError("You cannot assign an ean_code to an UMBRELLA. It needs to be BUNDLE or SIMPLE")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('product', 'ean_code', 'inherit_to')
        constraints = [
            models.UniqueConstraint(
                fields=['multi_tenant_company', 'ean_code'],
                name='unique_ean_code_per_tenant',
                condition=models.Q(ean_code__isnull=False),
                violation_error_message=_("Ean code already exists") # for now this will not apply but it can in the future https://github.com/django/django/pull/17723
            ),

            models.CheckConstraint(
                check=(
                    models.Q(ean_code__isnull=False) |
                    models.Q(product__isnull=False) |
                    models.Q(inherit_to__isnull=False)
                ),
                name='ean_code_or_product_to_not_null'
            )
        ]
        search_terms = ['ean_code']
