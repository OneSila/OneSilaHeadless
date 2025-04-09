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
        if hasattr(remote_product, 'configurator') and remote_product.configurator:
            remote_product.configurator.update_if_needed(send_sync_signal=True)

@db_task()
def update_configurators_for_product_property_db_task(parent_product_id, property_id):
    from sales_channels.models import RemoteProduct
    from products.models import Product
    from properties.models import Property

    parent_product = Product.objects.get(id=parent_product_id)
    property = Property.objects.get(id=property_id)

    product_rule = parent_product.get_product_rule()
    optional_properties = parent_product.get_optional_in_configurator_properties(product_rule)

    if property not in optional_properties.values_list('property', flat=True):
        return  # safety exit

    remote_products = RemoteProduct.objects.filter(
        local_instance=parent_product,
        multi_tenant_company=parent_product.multi_tenant_company
    )

    for remote_product in remote_products.iterator():
        if remote_product.configurator:
            remote_product.configurator.update_if_needed(rule=product_rule, send_sync_signal=True)
