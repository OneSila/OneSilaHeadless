from huey.contrib.djhuey import db_task
from products.product_types import CONFIGURABLE

# @TODO: Create factories for this tasks
@db_task()
def update_configurators_for_rule_db_task(rule):
    from products.models import Product
    from .models import RemoteProduct

    # Step 1: Filter products by the properties rule
    products = Product.objects.filter(type=CONFIGURABLE).filter_by_properties_rule(rule=rule)

    # Step 2: Filter out products with missing information
    products_with_valid_info = products.filter(inspector__has_missing_information=False)

    # Step 3: Retrieve remote products that are not variations and belong to the same tenant
    remote_products = RemoteProduct.objects.filter(
        local_instance_id__in=products_with_valid_info.values_list('id', flat=True),
        is_variation=False,
        multi_tenant_company=rule.multi_tenant_company
    )

    # Step 4: Iterate through remote products and update configurators
    for remote_product in remote_products.iterator():
        try:
            if remote_product.configurator:
                remote_product.configurator.update_if_needed(rule=rule, send_sync_signal=True)
        except RemoteProduct.configurator.RelatedObjectDoesNotExist:
            pass

@db_task()
def update_configurators_for_parent_product_db_task(parent_product):
    from sales_channels.models import RemoteProduct

    # Step 1: Retrieve remote products for the parent product and the multi-tenant company
    remote_products = RemoteProduct.objects.filter(
        local_instance=parent_product,
        is_variation=False,
        multi_tenant_company=parent_product.multi_tenant_company
    )

    # Step 2: Iterate through remote products and update configurators
    for remote_product in remote_products.iterator():
        if remote_product.configurator:
            remote_product.configurator.update_if_needed(send_sync_signal=True)

@db_task()
def update_configurators_for_product_property_db_task(product, property):
    from sales_channels.models import RemoteProduct
    from products.models import Product

    # Step 1: Get all parent product IDs where this product is a variation
    parent_product_ids = product.configurablevariation_through_variations.values_list('parent_id', flat=True)

    # Step 2: Retrieve all parent products in a single query
    parent_products = Product.objects.filter(id__in=parent_product_ids)

    # Step 3: Iterate through each parent product and check if we need to update the configurator
    for parent_product in parent_products:
        # Get the product rule for the parent product
        product_rule = parent_product.get_product_rule()

        # Check if the property is optional in the configurator
        optional_properties_in_configurator = parent_product.get_optional_in_configurator_properties(product_rule)
        if property not in optional_properties_in_configurator.values_list('property', flat=True):
            continue  # Skip if the property is not optional in configurator

        # Step 4: Retrieve remote products for the parent product
        remote_products = RemoteProduct.objects.filter(
            local_instance=parent_product,
            multi_tenant_company=parent_product.multi_tenant_company
        )

        # Step 5: Iterate through remote products and update configurators
        for remote_product in remote_products.iterator():
            if remote_product.configurator:
                remote_product.configurator.update_if_needed(rule=product_rule, send_sync_signal=True)