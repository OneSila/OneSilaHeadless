from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from core.models import MultiTenantCompany
from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=MultiTenantCompany)
def create_default_product_type_property(sender, instance, created, **kwargs):
    if created:
        Property.objects.create_product_type(instance)


@receiver(post_save, sender=PropertyTranslation)
def properties__property_translation__post_save(sender, instance, created, **kwargs):

    if created and not instance.property.internal_name:
        instance.property.internal_name = slugify(instance.name).replace('-', '_')
        instance.property.save(update_fields=['internal_name'])
