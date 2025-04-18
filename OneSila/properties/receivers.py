from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from core.models import MultiTenantCompany
from core.signals import post_create, post_update
from properties.models import Property, PropertyTranslation, PropertySelectValue, ProductProperty, PropertySelectValueTranslation, ProductPropertiesRule

import logging

from properties.signals import product_properties_rule_rename, product_properties_rule_created

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

@receiver(post_create, sender=PropertySelectValue)
def properties__property_select_value__create_rule(sender, instance, **kwargs):
    """
    Custom signal to create ProductPropertiesRule automatically if the property is a product_type
    after a PropertySelectValue is created.
    """
    if instance.property.is_product_type:
        rule = ProductPropertiesRule.objects.create(
            product_type=instance,
            multi_tenant_company=instance.multi_tenant_company
        )
        product_properties_rule_created.send(sender=rule.__class__, instance=rule)

@receiver(post_delete, sender=ProductPropertiesRule)
def delete_product_type_property_select_value(sender, instance, **kwargs):
    """
    After a ProductPropertiesRule is deleted force delete the associated PropertySelectValue to avoid orphaned records.
    """
    value = instance.product_type
    value.delete(force_delete=True)


@receiver(pre_delete, sender=PropertySelectValue)
def prevent_property_select_value_deletion(sender, instance, **kwargs):

    if ProductProperty.objects.filter(value_multi_select=instance).exists():
        raise ValidationError(
            _("This value cannot be deleted because it is used in as a product property multi-select field.")
        )
