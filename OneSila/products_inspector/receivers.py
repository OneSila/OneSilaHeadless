from django.db.models.signals import post_delete, m2m_changed
from django.dispatch import receiver
from core.decorators import trigger_signal_for_dirty_fields
from core.schema.core.subscriptions import refresh_subscription_receiver
from core.signals import post_create, post_update, mutation_update, mutation_create
from eancodes.signals import ean_code_released_for_product
from products.models import Product
from products_inspector.constants import HAS_IMAGES_ERROR, MISSING_PRICES_ERROR, INACTIVE_BUNDLE_ITEMS_ERROR, \
    MISSING_BUNDLE_ITEMS_ERROR, MISSING_VARIATION_ERROR, MISSING_EAN_CODE_ERROR, \
    MISSING_PRODUCT_TYPE_ERROR, MISSING_REQUIRED_PROPERTIES_ERROR, MISSING_OPTIONAL_PROPERTIES_ERROR, MISSING_STOCK_ERROR, \
    MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR, VARIATION_MISMATCH_PRODUCT_TYPE_ERROR, ITEMS_MISMATCH_PRODUCT_TYPE_ERROR, \
    ITEMS_MISSING_MANDATORY_INFORMATION_ERROR, VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR, \
    DUPLICATE_VARIATIONS_ERROR, NON_CONFIGURABLE_RULE_ERROR
from products_inspector.models import InspectorBlock, Inspector
from products_inspector.signals import inspector_block_refresh, inspector_missing_info_detected, inspector_missing_info_resolved
from properties.signals import product_properties_rule_created, product_properties_rule_updated


# BASIC RECEIVERS FOR FUNCTIONALITY ---------------------------------------------
@receiver(post_create, sender='products.Product')
@receiver(post_create, sender='products.SimpleProduct')
@receiver(post_create, sender='products.ConfigurableProduct')
@receiver(post_create, sender='products.BundleProduct')
def products_inspector__inspector__product_created(sender, instance, **kwargs):
    """
    When currencies change rates, most likely your prices need an update as well.
    """
    from .flows.inspector import inspector_creation_flow
    inspector_creation_flow(instance)


@receiver(post_update, sender=InspectorBlock)
@receiver(post_delete, sender=InspectorBlock)
def products_inspector__inspector_block__subscription__post_save(sender, instance, **kwargs):
    refresh_subscription_receiver(instance.inspector)


@receiver(post_update, sender=Inspector)
def products_inspector__inspector__subscription__post_save(sender, instance, **kwargs):
    refresh_subscription_receiver(instance.product)


@receiver(inspector_block_refresh, sender=Inspector)
def products_inspector__inspector__inspector_sync_block_by_error_code(sender, instance, **kwargs):
    from .flows.inspector_block import inspector_sync_block_by_error_code_flow
    error_code = kwargs.pop('error_code')
    inspector_sync_block_by_error_code_flow(instance, error_code, **kwargs)


# TRIGGERS FOR HAS_IMAGES_ERROR -------------------------------------------------

@receiver(post_create, sender='media.MediaProductThrough')
@receiver(post_delete, sender='media.MediaProductThrough')
def products_inspector__inspector__trigger_block_has_images(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.product.inspector.__class__, instance=instance.product.inspector, error_code=HAS_IMAGES_ERROR, run_async=False)


# MISSING_PRICES_ERROR ----------------------------------------------------------

@receiver(post_update, sender='products.Product')
@receiver(post_update, sender='products.SimpleProduct')
@receiver(post_update, sender='products.BundleProduct')
@trigger_signal_for_dirty_fields('active')
def products_inspector__inspector__trigger_block_product_active_change(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.inspector.__class__, instance=instance.inspector, error_code=MISSING_PRICES_ERROR, run_async=False)


@receiver(post_create, sender='sales_prices.SalesPrice')
@receiver(post_delete, sender='sales_prices.SalesPrice')
def products_inspector__inspector__trigger_block_missing_prices_sales_price_change(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.product.inspector.__class__, instance=instance.product.inspector, error_code=MISSING_PRICES_ERROR,
                                 run_async=False)


# INACTIVE_BUNDLE_ITEMS_ERROR & INACTIVE_BILL_OF_MATERIALS_ERROR ---------------
# MISSING_BUNDLE_ITEMS_ERROR  --------------------------------------------------
# MISSING_VARIATION_ERROR  -----------------------------------------------------

@receiver(post_create, sender='products.BundleVariation')
@receiver(post_delete, sender='products.BundleVariation')
def products_inspector__inspector__trigger_block_bom_change(sender, instance, **kwargs):
    from products_inspector.flows.inspector_block import recursively_check_components

    error_codes = [ INACTIVE_BUNDLE_ITEMS_ERROR]
    recursively_check_components(instance.parent, add_recursive_bundle=True, add_recursive_bom=True, add_recursive_variations=False, error_codes=error_codes)

    inspector_block_refresh.send(sender=instance.parent.inspector.__class__, instance=instance.parent.inspector, error_code=MISSING_BUNDLE_ITEMS_ERROR,
                                 run_async=False)


@receiver(post_update, sender='products.Product')
@receiver(post_update, sender='products.SimpleProduct')
@receiver(post_update, sender='products.BundleProduct')
@trigger_signal_for_dirty_fields('active')
def products_inspector__inspector__trigger_block_bundle_items_component_active_status_change(sender, instance, **kwargs):
    from products_inspector.flows.inspector_block import recursively_check_components

    error_codes = [INACTIVE_BUNDLE_ITEMS_ERROR, MISSING_VARIATION_ERROR]
    recursively_check_components(instance, add_recursive_bundle=True, add_recursive_bom=True, add_recursive_variations=True, error_codes=error_codes)


@receiver(post_create, sender='products.ConfigurableVariation')
@receiver(post_delete, sender='products.ConfigurableVariation')
def products_inspector__inspector__trigger_block_parent_variations_change(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.parent.inspector.__class__, instance=instance.parent.inspector, error_code=MISSING_VARIATION_ERROR,
                                 run_async=False)


# MISSING_SUPPLIER_PRODUCTS_ERROR  ---------------------------------------------

# @receiver(mutation_update, sender='products.Product')
# def products_inspector__inspector__trigger_block_supplier_products_mutation_change(sender, instance, **kwargs):
#     for base_product in instance.base_products.all().iterator():
#         inspector_block_refresh.send(sender=base_product.inspector.__class__, instance=base_product.inspector, error_code=MISSING_STOCK_ERROR, run_async=False)


# MISSING_EAN_CODE_ERROR  ------------------------------------------------------
@receiver(ean_code_released_for_product, sender='products.Product')
@receiver(ean_code_released_for_product, sender='products.SimpleProduct')
@receiver(ean_code_released_for_product, sender='products.BundleProduct')
def products_inspector__inspector__trigger_block_ean_code_released(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.inspector.__class__, instance=instance.inspector, error_code=MISSING_EAN_CODE_ERROR, run_async=False)


@receiver(post_update, sender='eancodes.EanCode')
@receiver(post_create, sender='eancodes.EanCode')
def products_inspector__inspector__trigger_block_ean_product_change(sender, instance, **kwargs):
    if instance.product is not None:
        product = instance.product
        inspector_block_refresh.send(sender=product.inspector.__class__, instance=product.inspector, error_code=MISSING_EAN_CODE_ERROR, run_async=False)

@receiver(post_delete, sender='eancodes.EanCode')
def products_inspector__inspector__trigger_block_ean_product_change_on_delete(sender, instance, **kwargs):
    if instance.product is not None:
        product = instance.product
        inspector_block_refresh.send(sender=product.inspector.__class__, instance=product.inspector, error_code=MISSING_EAN_CODE_ERROR, run_async=False)

# MISSING_PRODUCT_TYPE_ERROR  ------------------------------------------------------
# MISSING_REQUIRED_PROPERTIES_ERROR  -----------------------------------------------
# MISSING_OPTIONAL_PROPERTIES_ERROR  -----------------------------------------------

@receiver(post_delete, sender='properties.ProductProperty')
@receiver(post_update, sender='properties.ProductProperty')
@receiver(post_create, sender='properties.ProductProperty')
def products_inspector__inspector__trigger_block_product_properties_change(sender, instance, **kwargs):

    if not hasattr(instance.product, 'inspector'):
        return

    inspector_block_refresh.send(sender=instance.product.inspector.__class__,
                                 instance=instance.product.inspector,
                                 error_code=MISSING_PRODUCT_TYPE_ERROR,
                                 run_async=False)

    inspector_block_refresh.send(sender=instance.product.inspector.__class__,
                                 instance=instance.product.inspector,
                                 error_code=MISSING_REQUIRED_PROPERTIES_ERROR,
                                 run_async=False)

    inspector_block_refresh.send(sender=instance.product.inspector.__class__,
                                 instance=instance.product.inspector,
                                 error_code=MISSING_OPTIONAL_PROPERTIES_ERROR,
                                 run_async=False)

# MISSING_STOCK_ERROR  --------------------------------------------------

@receiver(post_update, sender='products.Product')
@receiver(post_update, sender='products.SimpleProduct')
@trigger_signal_for_dirty_fields('active', 'allow_backorder')
def products_inspector__inspector__trigger_block_product_active_or_allow_backorder_change(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.inspector.__class__, instance=instance.inspector, error_code=MISSING_STOCK_ERROR, run_async=False)


# @receiver(post_create, sender='inventory.Inventory')
# @receiver(post_delete, sender='inventory.Inventory')
# @receiver(post_update, sender='inventory.Inventory')
# def products_inspector__inspector__trigger_block_inventory_change(sender, instance, **kwargs):
#     from products.product_types import SUPPLIER
#
#     if instance.product.type == SUPPLIER:
#         for product in instance.product.base_products.all().iterator():
#             inspector_block_refresh.send(sender=product.inspector.__class__, instance=product.inspector, error_code=MISSING_STOCK_ERROR, run_async=False)


# MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR  ----------------------------------

@receiver(post_create, sender='sales_prices.SalesPriceListItem')
@receiver(post_delete, sender='sales_prices.SalesPriceListItem')
def products_inspector__inspector__trigger_block_sales_pricelist_item_create(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.product.inspector.__class__, instance=instance.product.inspector,
                                 error_code=MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR, run_async=False)


@receiver(post_update, sender='sales_prices.SalesPriceListItem')
@trigger_signal_for_dirty_fields('price_override')
def products_inspector__inspector__trigger_block_sales_pricelist_item_update(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.product.inspector.__class__, instance=instance.product.inspector,
                                 error_code=MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR, run_async=False)


@receiver(post_update, sender='sales_prices.SalesPriceList')
@trigger_signal_for_dirty_fields('auto_update_prices')
def products_inspector__inspector__trigger_block_sales_pricelist_update(sender, instance, **kwargs):
    for item in instance.salespricelistitem_set.all().iterator():
        inspector_block_refresh.send(sender=item.product.inspector.__class__, instance=item.product.inspector,
                                     error_code=MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR, run_async=False)


@receiver(post_delete, sender='sales_prices.SalesPriceList')
def products_inspector__inspector__trigger_block_sales_pricelist_delete(sender, instance, **kwargs):
    for item in instance.salespricelistitem_set.all().iterator():
        inspector_block_refresh.send(sender=item.product.inspector.__class__, instance=item.product.inspector,
                                     error_code=MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR, run_async=False)


# VARIATION_MISMATCH_PRODUCT_TYPE_ERROR  ----------------------------------
# ITEMS_MISMATCH_PRODUCT_TYPE_ERROR  --------------------------------------
# ITEMS_MISSING_MANDATORY_INFORMATION_ERROR  ------------------------------
# VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR  -------------------------

@receiver(post_delete, sender='properties.ProductProperty')
@receiver(post_create, sender='properties.ProductProperty')
@receiver(post_update, sender='properties.ProductProperty')
def products_inspector__inspector__trigger_block_product_type_variations_mismatch(sender, instance, **kwargs):
    from products.models import ConfigurableVariation, BundleVariation

    if not instance.property.is_product_type:
        return

    if not hasattr(instance.product, 'inspector'):
        return

    product = instance.product
    error_codes_to_trigger = [VARIATION_MISMATCH_PRODUCT_TYPE_ERROR,
                              ITEMS_MISMATCH_PRODUCT_TYPE_ERROR,
                              MISSING_EAN_CODE_ERROR,
                              DUPLICATE_VARIATIONS_ERROR,
                              NON_CONFIGURABLE_RULE_ERROR]

    for error_code in error_codes_to_trigger:
        inspector_block_refresh.send(sender=product.inspector.__class__,
                                     instance=product.inspector,
                                     error_code=error_code,
                                     run_async=False)

    for variation in ConfigurableVariation.objects.filter(variation=product).iterator():
        inspector_block_refresh.send(sender=variation.parent.inspector.__class__,
                                     instance=variation.parent.inspector,
                                     error_code=VARIATION_MISMATCH_PRODUCT_TYPE_ERROR,
                                     run_async=False)

    for item in BundleVariation.objects.filter(variation=product).iterator():
        inspector_block_refresh.send(sender=item.parent.inspector.__class__,
                                     instance=item.parent.inspector,
                                     error_code=ITEMS_MISMATCH_PRODUCT_TYPE_ERROR,
                                     run_async=False)


@receiver(post_create, sender='products.ConfigurableVariation')
@receiver(post_delete, sender='products.ConfigurableVariation')
@receiver(post_create, sender='products.BundleVariation')
@receiver(post_delete, sender='products.BundleVariation')
def products_inspector__inspector__trigger_block_product_mismatch_variation_changes(sender, instance, **kwargs):
    inspector_block_refresh.send(sender=instance.parent.inspector.__class__,
                                 instance=instance.parent.inspector,
                                 error_code=VARIATION_MISMATCH_PRODUCT_TYPE_ERROR,
                                 run_async=False)

    inspector_block_refresh.send(sender=instance.parent.inspector.__class__,
                                 instance=instance.parent.inspector,
                                 error_code=ITEMS_MISMATCH_PRODUCT_TYPE_ERROR,
                                 run_async=False)

    inspector_block_refresh.send(sender=instance.parent.inspector.__class__,
                                 instance=instance.parent.inspector,
                                 error_code=ITEMS_MISSING_MANDATORY_INFORMATION_ERROR,
                                 run_async=False)

    inspector_block_refresh.send(sender=instance.parent.inspector.__class__,
                                 instance=instance.parent.inspector,
                                 error_code=VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR,
                                 run_async=False)


    inspector_block_refresh.send(sender=instance.parent.inspector.__class__,
                                 instance=instance.parent.inspector,
                                 error_code=DUPLICATE_VARIATIONS_ERROR,
                                 run_async=False)


@receiver(inspector_missing_info_detected, sender='products.Product')
@receiver(inspector_missing_info_detected, sender='products.SimpleProduct')
@receiver(inspector_missing_info_detected, sender='products.BundleProduct')
@receiver(inspector_missing_info_resolved, sender='products.Product')
@receiver(inspector_missing_info_resolved, sender='products.SimpleProduct')
@receiver(inspector_missing_info_resolved, sender='products.BundleProduct')
def products_inspector__inspector__trigger_block_product_inspector_change(sender, instance, **kwargs):
    from products.models import ConfigurableVariation, BundleVariation

    for variation in ConfigurableVariation.objects.filter(variation=instance).iterator():
        inspector_block_refresh.send(sender=variation.parent.inspector.__class__,
                                     instance=variation.parent.inspector,
                                     error_code=VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR,
                                     run_async=False)

    for item in BundleVariation.objects.filter(variation=instance).iterator():
        inspector_block_refresh.send(sender=item.parent.inspector.__class__,
                                     instance=item.parent.inspector,
                                     error_code=ITEMS_MISSING_MANDATORY_INFORMATION_ERROR,
                                     run_async=False)


@receiver(post_update, sender='products.Product')
@receiver(post_update, sender='products.SimpleProduct')
@receiver(post_update, sender='products.BundleProduct')
@trigger_signal_for_dirty_fields('active')
def products_inspector__inspector__trigger_block_product_inspector_because_of_active_status_change(sender, instance, **kwargs):
    from products.models import ConfigurableVariation

    # bundle and manufacturable are not allowed to have non active variations at all
    # so making an item / bom active / inactive don't have any effect (remove this error but add the other one so it won't turn green)
    for variation in ConfigurableVariation.objects.filter(variation=instance).iterator():
        inspector_block_refresh.send(sender=variation.parent.inspector.__class__,
                                     instance=variation.parent.inspector,
                                     error_code=VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR,
                                     run_async=False)


@receiver(post_delete, sender='properties.ProductProperty')
@receiver(post_update, sender='properties.ProductProperty')
@receiver(post_create, sender='properties.ProductProperty')
def products_inspector__inspector__trigger_block_duplicate_variations_check(sender, instance, **kwargs):
    from products.models import ConfigurableVariation

    product = instance.product
    for variation in ConfigurableVariation.objects.filter(variation=product).iterator():
        parent = variation.parent
        properties_required_in_configurator = parent.get_configurator_properties().values_list('property_id', flat=True)
        if instance.property.id in properties_required_in_configurator:
            inspector_block_refresh.send(sender=parent.inspector.__class__,
                                         instance=parent.inspector,
                                         error_code=DUPLICATE_VARIATIONS_ERROR,
                                         run_async=False)


@receiver(product_properties_rule_created, sender='properties.ProductPropertiesRule')
@receiver(product_properties_rule_updated, sender='properties.ProductPropertiesRule')
def products_inspector__inspector__trigger_block_rule_changed(sender, instance, **kwargs):
    from .tasks import trigger_rule_dependent_inspector_blocks_task

    trigger_rule_dependent_inspector_blocks_task(instance.id)


@receiver(post_delete, sender='properties.ProductPropertiesRule')
def products_inspector__inspector__trigger_block_rule_deleted(sender, instance, **kwargs):
    from .tasks import trigger_rule_dependent_inspector_blocks_delete_task

    trigger_rule_dependent_inspector_blocks_delete_task(instance)
