from core.schema.core.subscriptions import refresh_subscription_receiver
from products_inspector.factories.inspector_block import InspectorBlockFactoryRegistry
import logging


logger = logging.getLogger(__name__)
def inspector_block_sync_flow(block):
    block_factory = InspectorBlockFactoryRegistry.get_factory(block.error_code)(block, save_inspector=True)
    block_factory.run()

def inspector_sync_block_by_error_code_flow(inspector, error_code, **kwargs):
    from ..tasks import resync_inspector_block_task
    """
    Synchronizes a specific block within an inspector based on the given error code.
    """
    # Find the block with the given error code within the inspector
    block = inspector.blocks.filter(error_code=error_code).first()

    if not block:
        logger.info(f"No block found with error code {error_code} for the given inspector.")
        return

    run_async = kwargs.get('run_async', False)

    if run_async:
        resync_inspector_block_task(block.id)
    else:
        # Get the appropriate factory and run it
        block_factory = InspectorBlockFactoryRegistry.get_factory(error_code)(block, save_inspector=True)
        block_factory.run()

def recursively_check_components(product, add_recursive_bom=True, add_recursive_bundle=True, add_recursive_variations=True, error_codes=None, run_async=False):
    from products_inspector.signals import inspector_block_refresh

    """
    Recursively check all BOM, Bundle, and ConfigurableVariation components where the given product is a variation.
    Trigger inspector refresh for the parent products and their ancestors based on the provided flags.
    """
    def refresh_inspector(parent_product):
        for error_code in error_codes:
            inspector_block_refresh.send(
                sender=parent_product.inspector.__class__,
                instance=parent_product.inspector,
                error_code=error_code,
                run_async=run_async
            )

    def add_recursive_bom_check(prod):
        from products.models import BillOfMaterial

        bill_of_materials = BillOfMaterial.objects.filter(variation=prod).iterator()
        for bill_of_material in bill_of_materials:
            parent_product = bill_of_material.parent
            refresh_inspector(parent_product)
            recursively_check_variations(parent_product)

    def add_recursive_bundle_check(prod):
        from products.models import BundleVariation

        bundle_variations = BundleVariation.objects.filter(variation=prod).iterator()
        for bundle_variation in bundle_variations:
            parent_product = bundle_variation.parent
            refresh_inspector(parent_product)
            recursively_check_variations(parent_product)

    def add_recursive_variations_check(prod):
        from products.models import ConfigurableVariation

        parent_variations = ConfigurableVariation.objects.filter(variation=prod).iterator()
        for parent_variation in parent_variations:
            parent_product = parent_variation.parent
            refresh_inspector(parent_product)
            recursively_check_variations(parent_product)

    def recursively_check_variations(prod):
        if add_recursive_bom:
            add_recursive_bom_check(prod)

        if add_recursive_bundle:
            add_recursive_bundle_check(prod)

        if add_recursive_variations:
            add_recursive_variations_check(prod)

    if error_codes is None:
        error_codes = []
        return

    refresh_inspector(product)
    recursively_check_variations(product)


def trigger_product_inspectors_for_rule_flow(rule):
    from products.models import Product
    from ..constants import MISSING_REQUIRED_PROPERTIES_ERROR, MISSING_OPTIONAL_PROPERTIES_ERROR, DUPLICATE_VARIATIONS_ERROR
    from products_inspector.signals import inspector_block_refresh

    rule_dependent_blocks = [MISSING_REQUIRED_PROPERTIES_ERROR,
                            MISSING_OPTIONAL_PROPERTIES_ERROR,
                            DUPLICATE_VARIATIONS_ERROR
                             ]

    for product in Product.objects.filter_by_properties_rule(rule=rule).iterator():
        for error_code in rule_dependent_blocks:
            inspector_block_refresh.send(sender=product.inspector.__class__,
                                         instance=product.inspector,
                                         error_code=error_code,
                                         run_async=False)

            refresh_subscription_receiver(product.inspector)