from core import models
from django.db import IntegrityError
from products.models import Product

import logging
logger = logging.getLogger(__name__)


class EanCode(models.Model):
    """
    Ean-codes are designed to be kept track of, for whoever buys their own codes.
    """
    product = models.OneToOneField(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ean_code = models.CharField(max_length=14, blank=True, null=True)

    def __str__(self):
        return "{}".format(self.ean_code)

    def save(self, *args, **kwargs):
        if self.product.is_umbrella():
            raise IntegrityError(f"You cannot assign an ean_code to an UMBRELLA.  It needs to be BUNDLE or VARIATION")

        super().save(*args, **kwargs)
