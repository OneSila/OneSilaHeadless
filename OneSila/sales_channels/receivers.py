from django.db.models.signals import post_delete, pre_delete
from core.signals import post_create, post_update
from inventory.models import Inventory
from .signals import (
    create_remote_property,
    update_remote_property,
    delete_remote_property, create_remote_property_select_value, update_remote_property_select_value, delete_remote_property_select_value,
    create_remote_product_property, update_remote_product_property, delete_remote_product_property, update_remote_inventory,
)
from django.dispatch import receiver
from properties.models import Property, PropertyTranslation, PropertySelectValueTranslation, PropertySelectValue, ProductProperty, \
    ProductPropertyTextTranslation


# ------------------------------------------------------------- SEND SIGNALS FOR PROPERTIES

@receiver(post_update, sender='properties.Property')
def sales_channels__property__post_update_receiver(sender, instance: Property, **kwargs):
    """
    Handles post-update events for the Property model.
    - Send create signal if `is_public_information` is True and relevant conditions are met.
    - Send update signal if specific fields change.
    - Send delete signal if `is_public_information` is set to False.
    """

    # Check for changes in `is_public_information`
    if instance.is_dirty_field('is_public_information'):
        if instance.is_public_information:
            # Send create signal if `is_public_information` changed to True
            create_remote_property.send(sender=instance.__class__, instance=instance)
        else:
            # Send delete signal if `is_public_information` changed to False
            delete_remote_property.send(sender=instance.__class__, instance=instance)

    # Check if `add_to_filters` is in dirty fields for an update signal
    if instance.is_dirty_field('add_to_filters'):
        update_remote_property.send(sender=instance.__class__, instance=instance)


@receiver(pre_delete, sender='properties.Property')
def sales_channels__property__pre_delete_receiver(sender, instance: Property, **kwargs):
    """
    Handles pre-delete events for the Property model to send delete signals.
    This is done pre-delete to ensure the remote instance is managed correctly before cascade deletes occur.
    """
    if instance.is_public_information:
        delete_remote_property.send(sender=instance.__class__, instance=instance)


# Receiver for PropertyTranslation model
@receiver(post_create, sender='properties.PropertyTranslation')
def sales_channels__property_translation__post_create_receiver(sender, instance: PropertyTranslation, **kwargs):
    """
    Handles post-create events for the PropertyTranslation model.
    - Send create signal if it's the first translation.
    """
    translation_count = PropertyTranslation.objects.filter(property=instance.property).count()

    if translation_count == 1:
        # Send create signal only if this is the first translation
        create_remote_property.send(sender=instance.property.__class__, instance=instance.property)


@receiver(post_update, sender='properties.PropertyTranslation')
def sales_channels__property_translation__post_update_receiver(sender, instance: PropertyTranslation, **kwargs):
    """
    Handles post-update events for the PropertyTranslation model to send update signals.
    """
    update_remote_property.send(sender=instance.property.__class__, instance=instance.property)


@receiver(post_delete, sender='properties.PropertyTranslation')
def sales_channels__property_translation__post_delete_receiver(sender, instance: PropertyTranslation, **kwargs):
    """
    Handles post-delete events for the PropertyTranslation model to send update signals.
    """
    update_remote_property.send(sender=instance.property.__class__, instance=instance.property)


# ------------------------------------------------------------- SEND SIGNALS FOR PROPERTIES SELECT VALUE

@receiver(post_create, sender='properties.PropertySelectValueTranslation')
def sales_channels__property_select_value_translation__post_create_receiver(sender, instance: PropertySelectValueTranslation, **kwargs):
    """
    Handles post-create events for the PropertySelectValueTranslation model.
    - Sends a create signal if it's the first translation for a PropertySelectValue.
    - Sends an update signal for additional translations.
    """
    property_instance = instance.propertyselectvalue.property

    # Only send signals if the associated Property is marked as public information
    if property_instance.is_public_information:
        translation_count = PropertySelectValueTranslation.objects.filter(propertyselectvalue=instance.propertyselectvalue).count()

        if translation_count == 1:
            # Send create signal only if this is the first translation
            create_remote_property_select_value.send(sender=instance.propertyselectvalue.__class__, instance=instance.propertyselectvalue)
        else:
            # For additional translations, send an update signal
            update_remote_property_select_value.send(sender=instance.propertyselectvalue.__class__, instance=instance.propertyselectvalue)

@receiver(post_update, sender='properties.PropertySelectValueTranslation')
def sales_channels__property_select_value_translation__post_update_receiver(sender, instance: PropertySelectValueTranslation, **kwargs):
    """
    Handles post-update events for the PropertySelectValueTranslation model.
    - Sends an update signal on any translation update if the property is public information.
    """
    if instance.propertyselectvalue.property.is_public_information:
        update_remote_property_select_value.send(sender=instance.propertyselectvalue.__class__, instance=instance.propertyselectvalue)

@receiver(pre_delete, sender='properties.PropertySelectValueTranslation')
def sales_channels__property_select_value_translation__pre_delete_receiver(sender, instance: PropertySelectValueTranslation, **kwargs):
    """
    Handles pre-delete events for the PropertySelectValueTranslation model.
    - Sends an update signal on translation deletion if the property is public information.
    """
    if instance.propertyselectvalue.property.is_public_information:
        update_remote_property_select_value.send(sender=instance.propertyselectvalue.__class__, instance=instance.propertyselectvalue)

@receiver(post_update, sender='properties.PropertySelectValue')
def sales_channels__property_select_value__post_update_receiver(sender, instance: PropertySelectValue, **kwargs):
    """
    Handles post-update events for the PropertySelectValue model.
    - Sends an update signal when the image field is updated and the property is public information.
    """
    if instance.property.is_public_information and instance.is_dirty_field('image'):
        update_remote_property_select_value.send(sender=instance.__class__, instance=instance)

@receiver(pre_delete, sender='properties.PropertySelectValue')
def sales_channels__property_select_value__pre_delete_receiver(sender, instance: PropertySelectValue, **kwargs):
    """
    Handles pre-delete events for the PropertySelectValue model.
    - Sends a delete signal before the PropertySelectValue is deleted if the property is public information.
    """
    if instance.property.is_public_information:
        delete_remote_property_select_value.send(sender=instance.__class__, instance=instance)


# ------------------------------------------------------------- SEND SIGNALS FOR PRODUCT PROPERTIES VALUES

@receiver(post_create, sender='attributes.ProductProperty')
def sales_channels__product_property__post_create_receiver(sender, instance: ProductProperty, **kwargs):
    if instance.property.is_public_information:
        create_remote_product_property.send(sender=instance.__class__, instance=instance)

@receiver(post_update, sender='attributes.ProductProperty')
def sales_channels__product_property__post_update_receiver(sender, instance: ProductProperty, **kwargs):
    if instance.property.is_public_information:
        update_remote_product_property.send(sender=instance.__class__, instance=instance)

@receiver(pre_delete, sender='attributes.ProductProperty')
def sales_channels__product_property__pre_delete_receiver(sender, instance: ProductProperty, **kwargs):
    if instance.property.is_public_information:
        delete_remote_product_property.send(sender=instance.__class__, instance=instance)

@receiver(post_create, sender='attributes.ProductPropertyTextTranslation')
def sales_channels__product_property_text_translation__post_create_receiver(sender, instance: ProductPropertyTextTranslation, **kwargs):
    if instance.product_property.property.is_public_information:
        create_remote_product_property.send(sender=instance.product_property.__class__, instance=instance.product_property)

@receiver(post_update, sender='attributes.ProductPropertyTextTranslation')
def sales_channels__product_property_text_translation__post_update_receiver(sender, instance: ProductPropertyTextTranslation, **kwargs):
    if instance.product_property.property.is_public_information:
        update_remote_product_property.send(sender=instance.product_property.__class__, instance=instance.product_property)

@receiver(pre_delete, sender='attributes.ProductPropertyTextTranslation')
def sales_channels__product_property_text_translation__pre_delete_receiver(sender, instance: ProductPropertyTextTranslation, **kwargs):
    if instance.product_property.property.is_public_information:
        update_remote_product_property.send(sender=instance.product_property.__class__, instance=instance.product_property)


# ------------------------------------------------------------- SEND SIGNALS FOR INVENTORY

@receiver(post_create, sender='inventory.Inventory')
@receiver(post_update, sender='inventory.Inventory')
@receiver(post_delete, sender='inventory.Inventory')
def handle_inventory_changes(sender, instance: Inventory, **kwargs):
    """
    Handles post-create, post-update, and post-delete events for the Inventory model.
    - Sends an update signal for the associated product's inventory.
    """
    update_remote_inventory.send(sender=instance.product.__class__, instance=instance.product)