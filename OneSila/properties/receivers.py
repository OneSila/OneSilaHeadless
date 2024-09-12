from django.dispatch import receiver
from django.utils.text import slugify

from core.models import MultiTenantCompany
from core.signals import post_create, post_update
from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty, PropertySelectValueTranslation, ProductPropertiesRule

import logging

from properties.signals import product_properties_rule_rename

logger = logging.getLogger(__name__)


@receiver(post_create, sender=MultiTenantCompany)
def create_default_product_type_property(sender, instance, **kwargs):
    Property.objects.create_product_type(instance)


@receiver(post_create, sender=PropertyTranslation)
def properties__property_translation__post_save(sender, instance, **kwargs):

    if not instance.property.internal_name:
        instance.property.internal_name = slugify(instance.name).replace('-', '_')
        instance.property.save(update_fields=['internal_name'])

@receiver(post_update, sender=PropertySelectValueTranslation)
def properties__property_select_value_translation__rename_rule(sender, instance, **kwargs):

    property_instance = instance.propertyselectvalue.property
    if property_instance.is_product_type:

        try:
            rule = ProductPropertiesRule.objects.get(
                product_type=instance.propertyselectvalue,
                multi_tenant_company=property_instance.multi_tenant_company
            )
            product_properties_rule_rename.send(sender=rule.__class__, instance=rule)
        except ProductPropertiesRule.DoesNotExist:
            pass