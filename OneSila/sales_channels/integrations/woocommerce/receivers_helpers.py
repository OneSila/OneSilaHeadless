import logging
logger = logging.getLogger(__name__)


def allow_product_property(instance):
    allowed_type = instance.property.is_product_type or instance.property.add_to_filters
    is_public = instance.property.is_public_information

    if not allowed_type:
        logger.info(f"Skipping woocommerce__product_property__create for {instance.property.name} because it is not used for filters or is not a product-type")
        return False

    if not is_public:
        logger.info(f"Skipping woocommerce__product_property__create for {instance.property.name} because it is not public")
        return False

    return True
