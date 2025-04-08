from django.db.models.signals import post_delete, pre_delete, pre_save

from core.decorators import trigger_signal_for_dirty_fields
from core.schema.core.subscriptions import refresh_subscription_receiver
from core.signals import post_create, post_update, mutation_update
from eancodes.signals import ean_code_released_for_product
from inventory.models import Inventory
from media.models import Media
from properties.signals import product_properties_rule_configurator_updated
from sales_prices.models import SalesPriceListItem
from sales_prices.signals import price_changed
from .integrations.magento2.models import MagentoProduct
from .models import SalesChannelImport
# from .models import ImportProcess
from .models.sales_channels import SalesChannelViewAssign
from .signals import (
    create_remote_property,
    update_remote_property,
    delete_remote_property, create_remote_property_select_value, update_remote_property_select_value,
    delete_remote_property_select_value,
    create_remote_product_property, update_remote_product_property, delete_remote_product_property,
    update_remote_price, update_remote_product_content, remove_remote_product_variation, add_remote_product_variation,
    create_remote_image_association,
    update_remote_image_association, delete_remote_image_association, delete_remote_image, sales_channel_created,
    delete_remote_product,
    sales_view_assign_updated, create_remote_product, update_remote_product, sync_remote_product, update_remote_product_eancode,
)
from django.dispatch import receiver
from properties.models import Property, PropertyTranslation, PropertySelectValueTranslation, PropertySelectValue, ProductProperty, \
    ProductPropertyTextTranslation

@receiver(post_update, sender=SalesChannelImport)
def import_process_post_create_receiver(sender, instance: SalesChannelImport, **kwargs):

    sales_channel = instance.sales_channel
    if not sales_channel.first_import_complete:
        completed_imports_exists = SalesChannelImport.objects.filter(
            sales_channel=sales_channel,
            status=SalesChannelImport.STATUS_SUCCESS
        ).exists()

        if not sales_channel.first_import_complete and completed_imports_exists:
            sales_channel.first_import_complete = True
            sales_channel.save(update_fields=['first_import_complete'])

@receiver(pre_save, sender=SalesChannelImport)
def import_process_avoid_duplicate_pre_create_receiver(sender, instance: SalesChannelImport, **kwargs):
    from django.utils.translation import gettext_lazy as _

    sales_channel = instance.sales_channel
    if sales_channel.is_importing and not instance.pk:
        raise OverflowError(_("There is another import that is already happening. Please wait for it to finish first."))

@receiver(post_update, sender=SalesChannelImport)
@trigger_signal_for_dirty_fields('status')
def import_process_post_update_receiver(sender, instance: SalesChannelImport, **kwargs):
    from sales_channels.integrations.magento2.models import MagentoSalesChannel
    from sales_channels.integrations.magento2.tasks import magento_import_db_task

    sales_channel = instance.sales_channel.get_real_instance()
    if instance.status == SalesChannelImport.STATUS_PENDING:

        if isinstance(sales_channel, MagentoSalesChannel):
            magento_import_db_task(import_process=instance, sales_channel=sales_channel)


@receiver(post_update, sender=SalesChannelImport)
def syncing_current_import_percentage_real_time_sync__post_update_receiver(sender, instance, **kwargs):
    """
    Update real time percentage when is changed to the sales channe.
    """
    if instance.is_dirty_field('percentage') or instance.is_dirty_field('status'):
        refresh_subscription_receiver(instance.sales_channel)


@receiver(post_update, sender=MagentoProduct)
def syncing_current_percentage_real_time_sync__post_update_receiver(sender, instance, **kwargs):
    """
    Update real time syncing_current_percentage when is changed to the product.
    """
    if instance.is_dirty_field('syncing_current_percentage'):
        refresh_subscription_receiver(instance.local_instance)


@receiver(post_create, sender=SalesChannelViewAssign)
@receiver(post_update, sender=SalesChannelViewAssign)
@receiver(post_delete, sender=SalesChannelViewAssign)
def sales_channels__assign__added_or_remove_receiver(sender, instance, **kwargs):
    """
    Update real time syncing_current_percentage when is changed to the product.
    """
    refresh_subscription_receiver(instance.product)

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


@receiver(post_create, sender='properties.PropertyTranslation')
def sales_channels__property_translation__post_create_receiver(sender, instance: PropertyTranslation, **kwargs):
    """
    Handles post-create events for the PropertyTranslation model.
    - Send create signal if it's the first translation.
    """
    if not instance.property.is_public_information:
        return

    translation_count = PropertyTranslation.objects.filter(property=instance.property).count()
    if translation_count == 1:
        # Send create signal only if this is the first translation
        create_remote_property.send(sender=instance.property.__class__, instance=instance.property, language=instance.language)
    else:
        update_remote_property.send(sender=instance.property.__class__, instance=instance.property, language=instance.language)


@receiver(post_update, sender='properties.PropertyTranslation')
def sales_channels__property_translation__post_update_receiver(sender, instance: PropertyTranslation, **kwargs):
    """
    Handles post-update events for the PropertyTranslation model to send update signals.
    """
    update_remote_property.send(sender=instance.property.__class__, instance=instance.property, language=instance.language)


@receiver(post_delete, sender='properties.PropertyTranslation')
def sales_channels__property_translation__post_delete_receiver(sender, instance: PropertyTranslation, **kwargs):
    """
    Handles post-delete events for the PropertyTranslation model to send update signals.
    """
    translation_count = PropertyTranslation.objects.filter(property=instance.property).count()

    if translation_count > 0:
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
            create_remote_property_select_value.send(sender=instance.propertyselectvalue.__class__, instance=instance.propertyselectvalue, language=instance.language)
        else:
            # For additional translations, send an update signal
            update_remote_property_select_value.send(sender=instance.propertyselectvalue.__class__, instance=instance.propertyselectvalue, language=instance.language)

@receiver(post_update, sender='properties.PropertySelectValueTranslation')
def sales_channels__property_select_value_translation__post_update_receiver(sender, instance: PropertySelectValueTranslation, **kwargs):
    """
    Handles post-update events for the PropertySelectValueTranslation model.
    - Sends an update signal on any translation update if the property is public information.
    """
    if instance.propertyselectvalue.property.is_public_information:
        update_remote_property_select_value.send(sender=instance.propertyselectvalue.__class__, instance=instance.propertyselectvalue, language=instance.language)


@receiver(pre_delete, sender='properties.PropertySelectValueTranslation')
def sales_channels__property_select_value_translation__pre_delete_receiver(sender, instance: PropertySelectValueTranslation, **kwargs):
    """
    Handles pre-delete events for the PropertySelectValueTranslation model.
    - Sends an update signal on translation deletion if the property is public information.
    - If there's only one translation, no update signal is sent as the PropertySelectValue will be deleted.
    """
    property_instance = instance.propertyselectvalue.property

    # Check if the property is marked as public information
    if property_instance.is_public_information:
        # Count the translations for the current PropertySelectValue
        translation_count = PropertySelectValueTranslation.objects.filter(propertyselectvalue=instance.propertyselectvalue).count()

        # Only send an update signal if there are more than one translations
        if translation_count > 1:
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

@receiver(post_create, sender='properties.ProductProperty')
def sales_channels__product_property__post_create_receiver(sender, instance: ProductProperty, **kwargs):

    if instance.property.is_product_type:
        sync_remote_product.send(sender=instance.product.__class__, instance=instance.product)
        return

    # the properties with translations will be created when the translation is created
    if instance.property.is_public_information and instance.property.type not in Property.TYPES.TRANSLATED:
        create_remote_product_property.send(sender=instance.__class__, instance=instance)

@receiver(post_update, sender='properties.ProductProperty')
def sales_channels__product_property__post_update_receiver(sender, instance: ProductProperty, **kwargs):
    from .tasks import update_configurators_for_product_property_db_task

    if instance.property.is_product_type:
        sync_remote_product.send(sender=instance.product.__class__, instance=instance.product)
        return

    if instance.property.is_public_information:
        update_remote_product_property.send(sender=instance.__class__, instance=instance)

        update_configurators_for_product_property_db_task(instance.product, instance.property)

@receiver(mutation_update, sender='properties.ProductProperty')
def sales_channels__product_property__post_update_multiselect_receiver(sender, instance: ProductProperty, **kwargs):
    from .tasks import update_configurators_for_product_property_db_task

    if instance.property.is_product_type:
        sync_remote_product.send(sender=instance.product.__class__, instance=instance.product)
        return

    if instance.property.is_public_information and instance.property.type == Property.TYPES.MULTISELECT:
        update_remote_product_property.send(sender=instance.__class__, instance=instance)

        update_configurators_for_product_property_db_task(instance.product, instance.property)

@receiver(pre_delete, sender='properties.ProductProperty')
def sales_channels__product_property__pre_delete_receiver(sender, instance: ProductProperty, **kwargs):

    if instance.property.is_product_type:
        sync_remote_product.send(sender=instance.product.__class__, instance=instance.product)
        return

    if instance.property.is_public_information:
        delete_remote_product_property.send(sender=instance.__class__, instance=instance)

@receiver(post_create, sender='properties.ProductPropertyTextTranslation')
def sales_channels__product_property_text_translation__post_create_receiver(sender, instance: ProductPropertyTextTranslation, **kwargs):

    if instance.product_property.property.is_public_information:
        create_remote_product_property.send(sender=instance.product_property.__class__, instance=instance.product_property, language=instance.language)

@receiver(post_update, sender='properties.ProductPropertyTextTranslation')
def sales_channels__product_property_text_translation__post_update_receiver(sender, instance: ProductPropertyTextTranslation, **kwargs):

    if instance.product_property.property.is_public_information:
        update_remote_product_property.send(sender=instance.product_property.__class__, instance=instance.product_property, language=instance.language)

@receiver(post_delete, sender='properties.ProductPropertyTextTranslation')
def sales_channels__product_property_text_translation__pre_delete_receiver(sender, instance: ProductPropertyTextTranslation, **kwargs):

    exists = ProductPropertyTextTranslation.objects.filter(product_property=instance.product_property).exists()
    if instance.product_property.property.is_public_information and exists:
        update_remote_product_property.send(sender=instance.product_property.__class__, instance=instance.product_property)


# ------------------------------------------------------------- SEND SIGNALS FOR INVENTORY

# @receiver(post_create, sender='inventory.Inventory')
# @receiver(post_update, sender='inventory.Inventory')
# @receiver(post_delete, sender='inventory.Inventory')
# def sales_channels__inventory__update(sender, instance: Inventory, **kwargs):
#     """
#     Handles post-create, post-update, and post-delete events for the Inventory model.
#     - Sends an update signal for the associated product's inventory.
#     """
#     from products.product_types import SUPPLIER
#
#     if instance.product.type == SUPPLIER:
#         for product in instance.product.base_products.all().iterator():
#             update_remote_inventory.send(sender=product.__class__, instance=product)
#     else:
#         update_remote_inventory.send(sender=instance.product.__class__, instance=instance.product)

# ------------------------------------------------------------- SEND SIGNALS FOR PRICES

@receiver(post_create, sender='sales_channels.SalesChannelIntegrationPricelist')
def sales_channels__sales_channel_integration_pricelist__post_create_receiver(sender, instance, **kwargs):
    """
    Trigger a price change signal for all products using the price list when a new price list is added to a sales channel.
    """
    sales_channel = instance.sales_channel
    assigns = SalesChannelViewAssign.objects.filter(sales_channel=sales_channel, sales_channel__active=True)
    for assign in assigns:
        update_remote_price.send(sender=assign.product.__class__, instance=assign.product)

@receiver(post_delete, sender='sales_channels.SalesChannelIntegrationPricelist')
def sales_channels__sales_channel_integration_pricelist__post_delete_receiver(sender, instance, **kwargs):
    """
    Trigger a price change signal for all products using the price list when a price list is removed from a sales channel.
    """
    sales_channel = instance.sales_channel
    assigns = SalesChannelViewAssign.objects.filter(sales_channel=sales_channel, sales_channel__active=True)
    for assign in assigns:
        update_remote_price.send(sender=assign.product.__class__, instance=assign.product)


@receiver(post_update, sender='sales_prices.SalesPriceList')
def sales_channels__sales_price_list__post_update_receiver(sender, instance, **kwargs):
    """
    Trigger a price change signal for all products using the price list when the price list's dates are updated.
    """
    if instance.is_any_field_dirty(['start_date', 'end_date']):
        price_list_items = SalesPriceListItem.objects.filter(salespricelist=instance)
        for item in price_list_items:
            update_remote_price.send(sender=item.product.__class__, instance=item.product)


@receiver(post_delete, sender='sales_prices.SalesPriceList')
def sales_channels__sales_price_list__pre_delete_receiver(sender, instance, **kwargs):
    """
    Trigger a price change signal for all products using the price list when a price list is deleted.
    """
    price_list_items = SalesPriceListItem.objects.filter(salespricelist=instance)
    for item in price_list_items:
        update_remote_price.send(sender=item.product.__class__, instance=item.product)


@receiver(post_create, sender='sales_prices.SalesPriceListItem')
@receiver(post_update, sender='sales_prices.SalesPriceListItem')
@receiver(post_delete, sender='sales_prices.SalesPriceListItem')
def sales_channels__sales_price_list_item__post_create_receiver(sender, instance, **kwargs):
    update_remote_price.send(sender=instance.product.__class__, instance=instance.product)


@receiver(post_update, sender='sales_prices.SalesPrice')
def sales_channels__sales_price__post_update_receiver(sender, instance, **kwargs):
    """
    Trigger a price change signal when the product price or RRP is updated.
    """
    update_remote_price.send(sender=instance.product.__class__, instance=instance.product)

@receiver(price_changed, sender='products.Product')
def sales_channels__price_changed__receiver(sender, instance, **kwargs):
    """
    Handle the price_changed signal to check trigger the update_remote_price signal if so.
    """
    update_remote_price.send(sender=instance.__class__, instance=instance)

# ------------------------------------------------------------- SEND SIGNALS FOR PRODUCT CONTENT

@receiver(post_create, sender='products.ProductTranslation')
@receiver(post_update, sender='products.ProductTranslation')
def sales_channels__product_translation__post_create_update_receiver(sender, instance, **kwargs):
    """
    Trigger the update_remote_product_content signal for the associated product
    whenever a ProductTranslation is created, updated, or deleted.
    """
    update_remote_product_content.send(sender=instance.product.__class__, instance=instance.product, language=instance.language)


@receiver(post_delete, sender='products.ProductTranslation')
def sales_channels__product_translation__post_delete_receiver(sender, instance, **kwargs):
    """
    Trigger the update_remote_product_content signal for the associated product
    whenever a ProductTranslation is created, updated, or deleted.
    """
    update_remote_product_content.send(sender=instance.product.__class__, instance=instance.product)

# ------------------------------------------------------------- SEND SIGNALS FOR VARIATIONS

@receiver(post_create, sender='products.ConfigurableVariation')
def sales_channels__configurable_variation__post_create_receiver(sender, instance, **kwargs):
    """
    Handle post-create events for the ConfigurableVariation model.
    Sends a signal to add the variation to the remote product.
    """
    from .tasks import update_configurators_for_parent_product_db_task

    add_remote_product_variation.send(
        sender=instance.__class__,
        parent_product=instance.parent,
        variation_product=instance.variation
    )

    update_configurators_for_parent_product_db_task(instance.parent)

@receiver(post_delete, sender='products.ConfigurableVariation')
def sales_channels__configurable_variation__post_delete_receiver(sender, instance, **kwargs):
    """
    Handle post-delete events for the ConfigurableVariation model.
    Sends a signal to remove the variation from the remote product.
    """
    from .tasks import update_configurators_for_parent_product_db_task

    remove_remote_product_variation.send(
        sender=instance.__class__,
        parent_product=instance.parent,
        variation_product=instance.variation
    )

    update_configurators_for_parent_product_db_task(instance.parent)


# ------------------------------------------------------------- SEND SIGNALS FOR IMAGES

@receiver(post_create, sender='media.MediaProductThrough')
def sales_channels__media_product_through__post_create_receiver(sender, instance, **kwargs):
    """
    Handles the creation of MediaProductThrough instances.
    Sends a create_remote_image_association signal if the media type is IMAGE.
    """
    if instance.media.type == Media.IMAGE:
        create_remote_image_association.send(sender=instance.__class__, instance=instance)

@receiver(post_update, sender='media.MediaProductThrough')
def sales_channels__media_product_through__post_update_receiver(sender, instance, **kwargs):
    """
    Handles the update of MediaProductThrough instances.
    Sends an update_remote_image_association signal if the sort_order or is_main_image fields are changed
    and the media type is IMAGE.
    """
    if instance.media.type == Media.IMAGE and instance.is_any_field_dirty(['sort_order', 'is_main_image']):
        update_remote_image_association.send(sender=instance.__class__, instance=instance)

@receiver(pre_delete, sender='media.MediaProductThrough')
def sales_channels__media_product_through__post_delete_receiver(sender, instance, **kwargs):
    """
    Handles the deletion of MediaProductThrough instances.
    Sends a delete_remote_image_association signal if the media type is IMAGE.
    """
    if instance.media.type == Media.IMAGE:
        delete_remote_image_association.send(sender=instance.__class__, instance=instance)
        
@receiver(post_delete, sender='media.Media')
def sales_channels__media__post_delete_receiver(sender, instance, **kwargs):
    """
    Handles the deletion of Media instances.
    Sends a delete_remote_image signal if the media type is IMAGE.
    """
    if instance.type == Media.IMAGE:
        delete_remote_image.send(sender=instance.__class__, instance=instance)

# ------------------------------------------------------------- SEND SIGNALS FOR SALES CHANNEL


@receiver(post_create, sender='sales_channels.SalesChannel')
@receiver(post_create, sender='magento2.MagentoSalesChannel')
def sales_channels__sales_channel__post_create_receiver(sender, instance, **kwargs):
    """
    Handles the creation of SalesChannel instances.
    Sends the sales_channel_created signal when a new SalesChannel is created.
    """
    sales_channel_created.send(sender=instance.__class__, instance=instance)


# ------------------------------------------------------------- SEND SIGNALS FOR PRODUCT AND SALES CHANNEL ASSIGN

@receiver(post_create, sender='sales_channels.SalesChannelViewAssign')
def sales_channel_view_assign__post_create_receiver(sender, instance, **kwargs):
    """
    Handles the creation of SalesChannelViewAssign instances.
    - Sends create_remote_product if it's the first assignment for the product on the sales_channel.
    - Sends sales_view_assign_updated for any other creation.
    """
    # Count the number of assignments related to the same product and sales channel
    product_assign_count = SalesChannelViewAssign.objects.filter(
        product=instance.product,
        sales_channel=instance.sales_channel,
        sales_channel__active=True
    ).count()

    # during imports sales channels are not active this signal will be triggered but it should just be skipped
    if product_assign_count == 0:
        return

    if product_assign_count == 1:
        create_remote_product.send(sender=instance.__class__, instance=instance)
    else:
        # Otherwise, send sales_view_assign_updated signal
        sales_view_assign_updated.send(sender=instance.product.__class__, instance=instance.product, sales_channel=instance.sales_channel)


@receiver(post_delete, sender='sales_channels.SalesChannelViewAssign')
def sales_channel_view_assign__post_delete_receiver(sender, instance, **kwargs):
    """
    Handles the deletion of SalesChannelViewAssign instances.
    - Sends delete_remote_product if it's the last assignment for the product on the sales_channel.
    - Sends sales_view_assign_updated for any other deletion.
    """
    from sales_channels.models import SalesChannel
    from products.models import ConfigurableVariation
    # this is for CASCADE DELETE of sales chanel
    try:
        sales_channel = instance.sales_channel
    except SalesChannel.DoesNotExist:
        return


    # Count the number of assignments related to the same product and sales channel
    product_assign_count = SalesChannelViewAssign.objects.filter(
        product=instance.product,
        sales_channel=instance.sales_channel,
        sales_channel__active=True
    ).count()

    is_variation = ConfigurableVariation.objects.filter(variation=instance.product).exists()
    if product_assign_count == 0:
        # Last assignment removed for this sales_channel, send delete_remote_product signal
        delete_remote_product.send(sender=instance.__class__, instance=instance, is_variation=is_variation)
    else:
        # Otherwise, send sales_view_assign_updated signal
        sales_view_assign_updated.send(sender=instance.product.__class__, instance=instance.product, sales_channel=instance.sales_channel)

@receiver(post_update, sender='products.Product')
@receiver(post_update, sender='products.SimpleProduct')
@receiver(post_update, sender='products.ConfigurableProduct')
@receiver(post_update, sender='products.BundleProduct')
def sales_channels__product__post_update_receiver(sender, instance, **kwargs):
    """
    Handle post-update events for the product models.
    Sends update_remote_product signal if any of the fields 'active' or 'allow_backorder' are dirty.
    """
    # Check if any of the specified fields have changed
    if instance.is_any_field_dirty(['active', 'allow_backorder']):
        # Send update_remote_product signal
        update_remote_product.send(sender=instance.__class__, instance=instance)

@receiver(pre_delete, sender='products.Product')
@receiver(pre_delete, sender='products.SimpleProduct')
@receiver(pre_delete, sender='products.ConfigurableProduct')
@receiver(pre_delete, sender='products.BundleProduct')
def sales_channels__product__pre_delete_receiver(sender, instance, **kwargs):
    """
    Handle pre-delete events for the product models.
    Sends delete_remote_product signal before the product is deleted.
    """
    delete_remote_product.send(sender=instance.__class__, instance=instance)

@receiver(post_update, sender='products_inspector.Inspector')
def sales_channels__inspector__post_update_receiver(sender, instance, **kwargs):
    """
    Handle post-update events for the Inspector model.
    Sends sync_remote_product signal if 'has_missing_information' changes to False.
    """
    if instance.is_dirty_field('has_missing_information') and not instance.has_missing_information:
        sync_remote_product.send(sender=instance.product.__class__, instance=instance.product)
        
@receiver(product_properties_rule_configurator_updated, sender='properties.ProductPropertiesRule')
def sales_channels__configurator_rule_changed_receiver(sender, instance, **kwargs):
    from .tasks import update_configurators_for_rule_db_task
    
    update_configurators_for_rule_db_task(instance)


@receiver(post_update, sender='eancodes.EanCode')
@receiver(post_create, sender='eancodes.EanCode')
@receiver(post_delete, sender='eancodes.EanCode')
def sales_channels__ean_code_changed_receiver(sender, instance, **kwargs):
    from .tasks import update_configurators_for_rule_db_task

    product = instance.product
    if product:
        update_remote_product_eancode.send(sender=product.__class__, instance=product)

@receiver(ean_code_released_for_product, sender='products.Product')
@receiver(ean_code_released_for_product, sender='products.SimpleProduct')
@receiver(ean_code_released_for_product, sender='products.BundleProduct')
def sales_channels__ean_code_released_receiver(sender, instance, **kwargs):
    update_remote_product_eancode.send(sender=instance.__class__, instance=instance)