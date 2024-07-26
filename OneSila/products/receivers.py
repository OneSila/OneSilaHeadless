from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from core.schema.core.subscriptions import refresh_subscription_receiver
from products.models import Product, ProductTranslation, SupplierProduct


import logging
logger = logging.getLogger('__name__')


@receiver(post_save, sender=ProductTranslation)
def products__images__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance.product)


@receiver(post_save, sender=SupplierProduct)
@receiver(post_save, sender=Product)
def products__supplier_product__post_save__set_supplier(sender, instance, **kwargs):
    """
    When an supplier product is saved, we must at least make sure they are marked as a customer.
    """
    if instance.supplier:
        instance.supplier.set_is_supplier()
