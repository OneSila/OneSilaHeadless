from products.models import Product
from sales_channels.tasks import update_configurators_for_product_property_db_task


def update_configurator_if_needed_flow(product, property):

    parent_product_ids = product.configurablevariation_through_variations.values_list('parent_id', flat=True)

    # Step 2: Retrieve all parent products in a single query
    parent_products = Product.objects.filter(id__in=parent_product_ids)

    for parent_product in parent_products:
        update_configurators_for_product_property_db_task(parent_product.id, property.id)
