from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from products.models import Product, BundleProduct, UmbrellaProduct, SimpleProduct, ProductTranslation, \
    UmbrellaVariation, BundleVariation, DropshipProduct, ManufacturableProduct, SupplierProduct, BillOfMaterial
from media.models import MediaProductThrough

from core.schema.core.subscriptions import refresh_subscription_receiver

import logging
logger = logging.getLogger('__name__')

@receiver(post_save, sender=MediaProductThrough)
@receiver(post_delete, sender=MediaProductThrough)
def products__images__subscription__post_save(sender, instance, **kwargs):
    """
    This is to be sent on the every post_save or relevant signal
    """
    refresh_subscription_receiver(instance.product)

@receiver(post_save, sender=Product)
def translation__producttranslation__post_save(sender, instance, created, *args, **kwargs):
    """
    Whenever a new product is created, create the needed translation instance in the default company language.
    """
    # @TODO: FIX THIS! IS BROKEN!
    # language = instance.company.language
    # ProductTranslation.objects.get_or_create(product=instance, language=language)
    pass
