from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from products.models import Product, BundleProduct, UmbrellaProduct, ProductVariation, ProductTranslation, \
    UmbrellaVariation, BundleVariation

import logging
logger = logging.getLogger('__name__')


@receiver(post_save, sender=Product)
def translation__producttranslation__post_save(sender, instance, created, *args, **kwargs):
    """
    Whenever a new product is created, create the needed translation instance in the default language.
    """
    language = instance.company.language
    ProductTranslation.objects.get_or_create(product=instance, language=language)
