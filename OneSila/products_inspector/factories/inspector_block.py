from django.db import transaction
from django.db.models import Q

from core import models
from media.models import MediaProductThrough
from .inspector import InspectorCreateOrUpdateFactory, SaveInspectorMixin
from ..exceptions import InspectorBlockFailed
from products_inspector.constants import HAS_IMAGES_ERROR, MISSING_PRICES_ERROR, NONE, MISSING_VARIATION_ERROR, \
    MISSING_BUNDLE_ITEMS_ERROR, INACTIVE_BUNDLE_ITEMS_ERROR, MISSING_EAN_CODE_ERROR, \
    MISSING_PRODUCT_TYPE_ERROR, MISSING_REQUIRED_PROPERTIES_ERROR, MISSING_OPTIONAL_PROPERTIES_ERROR, MISSING_STOCK_ERROR, \
    MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR, VARIATION_MISMATCH_PRODUCT_TYPE_ERROR, \
    ITEMS_MISSING_MANDATORY_INFORMATION_ERROR, VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR, \
    DUPLICATE_VARIATIONS_ERROR, NON_CONFIGURABLE_RULE_ERROR, AMAZON_VALIDATION_ISSUES_ERROR, AMAZON_REMOTE_ISSUES_ERROR
from products_inspector.models import InspectorBlock
from products_inspector.signals import *
from ..constants import blocks

import logging
logger = logging.getLogger(__name__)


class InspectorBlockCreateOrUpdateFactory(InspectorCreateOrUpdateFactory):
    def __init__(self, inspector, error_code):
        super().__init__(inspector.product)
        self.inspector = inspector
        self.error_code = error_code
        self.product = inspector.product
        self.multi_tenant_company = inspector.multi_tenant_company

    def _create_or_update_block(self):
        """
        Creates or updates the InspectorBlock based on the error_code and product type.
        """
        target_field_key = self._get_target_field_key()

        if not target_field_key:
            logger.info(f"No applicable target field for product type {self.product.type}")
            return

        # Find the block configuration that matches the provided error code
        block_config = next((config for config in blocks if config['error_code'] == self.error_code), None)

        if not block_config:
            logger.info(f"No block configuration found for error code {self.error_code}")
            return

        target_field_value = block_config.get(target_field_key)

        if not target_field_value or target_field_value == NONE:
            logger.info(f"Product {self.product.sku} does not require block with error code {self.error_code}")
            return

        # Create or update the block
        block, created = InspectorBlock.objects.get_or_create(
            inspector=self.inspector,
            multi_tenant_company=self.multi_tenant_company,
            **block_config
        )

        if created:
            logger.info(f"Created InspectorBlock (error_code={self.error_code}) for product {self.product.sku}")
            block_factory = InspectorBlockFactoryRegistry.get_factory(self.error_code)(block, save_inspector=True)
            block_factory.run()
        else:
            logger.info(f"InspectorBlock (error_code={self.error_code}) already exists for product {self.product.sku}")

    def run(self):
        self._create_or_update_block()


class InspectorBlockFactoryRegistry:
    registry = {}

    @classmethod
    def register(cls, error_code):
        def decorator(factory_class):
            cls.registry[error_code] = factory_class
            return factory_class

        return decorator

    @classmethod
    def get_factory(cls, error_code):
        factory_class = cls.registry.get(error_code)
        if not factory_class:
            raise ValueError(f"No factory found for error code {error_code}")
        return factory_class


class InspectorBlockFactory(SaveInspectorMixin):
    def __init__(self, block, success_signal=None, failure_signal=None, save_inspector=True):
        self.block = block
        self.inspector = block.inspector
        self.product = block.inspector.product
        self.multi_tenant_company = self.product.multi_tenant_company
        self.previous_state = block.successfully_checked
        self.success_signal = success_signal
        self.failure_signal = failure_signal
        self.save_inspector_instance = save_inspector

    def preflight_approval(self):
        """
        Checks if the block should be inspected based on the product type and target field.
        """
        target_field_key = self.block.get_target_field_key()
        if not target_field_key:
            logger.info(f"Block {self.block.error_code} cannot be inspected: no matching target field.")
            return False

        target_value = getattr(self.block, target_field_key)
        if target_value == NONE:
            logger.info(f"Block {self.block.error_code} is not applicable for product {self.product.sku}.")
            return False

        return True

    def _check(self):
        raise NotImplementedError("Subclasses should implement this method based on the block's error code.")

    def _save_block(self, success_signal=None, failure_signal=None):
        """
        Saves the block state and triggers signals if the state changed.
        """
        try:
            self._check()
            self.block.successfully_checked = True
            logger.info(f"Block {self.block.error_code} successfully checked for product {self.product.sku}.")
        except InspectorBlockFailed as e:
            self.block.successfully_checked = False
            logger.info(f"Block {self.block.error_code} failed for product {self.product.sku}: {str(e)}")

        self.block.save()

        # Check if the state changed
        if self.previous_state != self.block.successfully_checked:
            if self.block.successfully_checked:
                if success_signal:
                    success_signal.send(sender=self.product.__class__, instance=self.product)
                    logger.info(f"Success signal sent for block {self.block.error_code} on product {self.product.sku}.")
            else:
                if failure_signal:
                    failure_signal.send(sender=self.product.__class__, instance=self.product)
                    logger.info(f"Failure signal sent for block {self.block.error_code} on product {self.product.sku}.")

    def _save_inspector(self):
        """
        Updates the inspector's overall state based on the blocks' states.
        """
        if not self.save_inspector_instance:
            logger.info(f"Saving the inspector is skipped..")
            return

        self.save_inspector()

    def run(self):
        """
        Runs the inspection block process.
        """
        if self.preflight_approval():
            self._save_block(success_signal=None, failure_signal=None)
            self._save_inspector()


@InspectorBlockFactoryRegistry.register(HAS_IMAGES_ERROR)
class HasImagesInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_has_images_success, failure_signal=inspector_has_images_failed, save_inspector=save_inspector)

    def _check(self):
        images_count = MediaProductThrough.objects.filter_multi_tenant(self.multi_tenant_company).filter(product=self.product).count()

        if self.product.is_configurable():
            if images_count == 0:
                raise InspectorBlockFailed("Product does not have required images.")
            return

        from sales_channels.models import SalesChannelViewAssign

        if SalesChannelViewAssign.objects.filter(multi_tenant_company=self.multi_tenant_company, product=self.product).exists():
            if images_count == 0:
                raise InspectorBlockFailed("Product does not have required images.")


@InspectorBlockFactoryRegistry.register(MISSING_PRICES_ERROR)
class MissingPricesInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_prices_success, failure_signal=inspector_missing_prices_failed, save_inspector=save_inspector)

    def _check(self):
        from sales_prices.models import SalesPrice

        if not self.product.active:
            return

        prices_qs = SalesPrice.objects.filter_multi_tenant(self.multi_tenant_company).filter(product=self.product)

        if not prices_qs.exists():
            raise InspectorBlockFailed("Product is missing default price.")

        # All entries are placeholders
        valid_prices_exist = prices_qs.filter(
            models.Q(price__isnull=False, price__gt=0) | models.Q(rrp__isnull=False, rrp__gt=0)
        ).exists()

        if not valid_prices_exist:
            raise InspectorBlockFailed("Product has only placeholder prices (RRP and Price are missing or zero).")


@InspectorBlockFactoryRegistry.register(INACTIVE_BUNDLE_ITEMS_ERROR)
class InactiveBundleItemsInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_inactive_bundle_items_success, failure_signal=inspector_inactive_bundle_items_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from products.models import BundleProduct
        if BundleProduct.objects.get_all_item_products(self.product).filter_multi_tenant(self.multi_tenant_company).filter(active=False).exists():
            raise InspectorBlockFailed(f"Product has inactive items components.")


@InspectorBlockFactoryRegistry.register(MISSING_VARIATION_ERROR)
class MissingVariationInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_variation_success, failure_signal=inspector_missing_variation_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from products.models import ConfigurableVariation
        if not ConfigurableVariation.objects.filter_multi_tenant(self.multi_tenant_company).filter(parent=self.product, variation__active=True).exists():
            raise InspectorBlockFailed(f"Configurable Product have no variation")


@InspectorBlockFactoryRegistry.register(MISSING_BUNDLE_ITEMS_ERROR)
class MissingBundleItemsInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_bundle_items_success, failure_signal=inspector_missing_bundle_items_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from products.models import BundleVariation
        if not BundleVariation.objects.filter_multi_tenant(self.multi_tenant_company).filter(parent=self.product).exists():
            raise InspectorBlockFailed(f"Bundle Product have no items")


8


@InspectorBlockFactoryRegistry.register(MISSING_EAN_CODE_ERROR)
class MissingEanCodeInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_ean_code_success, failure_signal=inspector_missing_ean_code_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from eancodes.models import EanCode

        rule = self.product.get_product_rule()
        if rule is None:
            return  # we cannot tell if this is necessary or not

        if not rule.require_ean_code:
            return  # if the rule doesn't require ean code we just skip

        if not EanCode.objects.filter_multi_tenant(self.multi_tenant_company).filter(product=self.product).exists():
            raise InspectorBlockFailed("Product is missing an EAN code.")


@InspectorBlockFactoryRegistry.register(MISSING_PRODUCT_TYPE_ERROR)
class MissingProductTypeInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_product_type_success, failure_signal=inspector_missing_product_type_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from properties.models import ProductProperty

        if not ProductProperty.objects.filter_multi_tenant(self.multi_tenant_company).filter(product=self.product, property__is_product_type=True).exists():
            raise InspectorBlockFailed("Product is missing a required product type property.")


@InspectorBlockFactoryRegistry.register(MISSING_REQUIRED_PROPERTIES_ERROR)
class MissingRequiredPropertiesInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_required_properties_success, failure_signal=inspector_missing_required_properties_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from properties.models import ProductProperty

        rule_item_properties_ids = self.product.get_required_properties(public_information_only=False).values_list('property_id', flat=True)
        product_properties = ProductProperty.objects.filter_multi_tenant(self.multi_tenant_company). \
            filter(product=self.product, property_id__in=rule_item_properties_ids)

        if product_properties.count() != rule_item_properties_ids.count():
            raise InspectorBlockFailed(f"Product is missing required propertes")


@InspectorBlockFactoryRegistry.register(MISSING_OPTIONAL_PROPERTIES_ERROR)
class MissingOptionalPropertiesInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_optional_properties_success, failure_signal=inspector_missing_optional_properties_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from properties.models import ProductProperty

        rule_item_properties_ids = self.product.get_optional_properties(public_information_only=False).values_list('property_id', flat=True)
        product_properties = ProductProperty.objects.filter_multi_tenant(self.multi_tenant_company). \
            filter(product=self.product, property_id__in=rule_item_properties_ids)

        if product_properties.count() != rule_item_properties_ids.count():
            raise InspectorBlockFailed(f"Product is missing optional propertes")


@InspectorBlockFactoryRegistry.register(MISSING_STOCK_ERROR)
class MissingStockInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_stock_success, failure_signal=inspector_missing_stock_failed,
                         save_inspector=save_inspector)

    def _check(self):
        # @TODO THIS NEEDS REFACTOR AFTER WE HAVE INVETORY IN A SIMPLE FORM
        pass


@InspectorBlockFactoryRegistry.register(MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR)
class MissingManualPriceListOverrideInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_missing_manual_pricelist_override_success, failure_signal=inspector_missing_manual_pricelist_override_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from sales_prices.models import SalesPriceListItem

        if SalesPriceListItem.objects.filter_multi_tenant(self.multi_tenant_company).\
                filter(salespricelist__auto_update_prices=False, product=self.product, price_override__isnull=True).exists():
            raise InspectorBlockFailed("Price have manual price list without a price override")


@InspectorBlockFactoryRegistry.register(VARIATION_MISMATCH_PRODUCT_TYPE_ERROR)
class VariationMismatchProductTypeInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_variation_mismatch_product_type_success, failure_signal=inspector_variation_mismatch_product_type_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from properties.models import ProductProperty
        from products.models import ConfigurableVariation

        product_type_value_id = ProductProperty.objects.filter(
            multi_tenant_company=self.multi_tenant_company,
            product=self.product,
            property__is_product_type=True
        ).values_list('value_select', flat=True).first()

        variation_ids = ConfigurableVariation.objects.filter_multi_tenant(self.multi_tenant_company).\
            filter(parent=self.product).values_list('variation_id', flat=True)

        variations_product_type_value = ProductProperty.objects.filter(multi_tenant_company=self.multi_tenant_company,
                                                                       product_id__in=variation_ids,
                                                                       property__is_product_type=True).\
            values_list('value_select', flat=True).distinct()

        if variations_product_type_value.count() == 0 or product_type_value_id is None:
            # this will be another error
            return

        if variations_product_type_value.count() != 1:
            raise InspectorBlockFailed("Variations product type mismatch")
        else:
            if variations_product_type_value.first() != product_type_value_id:
                raise InspectorBlockFailed("Variations product type mismatch")


@InspectorBlockFactoryRegistry.register(ITEMS_MISSING_MANDATORY_INFORMATION_ERROR)
class ItemsMissingMandatoryInformationInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_items_missing_mandatory_information_success, failure_signal=inspector_items_missing_mandatory_information_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from products.models import BundleVariation
        from ..models import Inspector

        items_ids = BundleVariation.objects.filter_multi_tenant(self.multi_tenant_company). \
            filter(parent=self.product).values_list('variation_id', flat=True)

        if Inspector.objects.filter_multi_tenant(self.multi_tenant_company).filter(product_id__in=items_ids, has_missing_information=True).exists():
            raise InspectorBlockFailed("Bundle items has missing information")


@InspectorBlockFactoryRegistry.register(VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR)
class VariationsMissingMandatoryInformationInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(block, success_signal=inspector_variations_missing_mandatory_information_success, failure_signal=inspector_variations_missing_mandatory_information_failed,
                         save_inspector=save_inspector)

    def _check(self):
        from products.models import ConfigurableVariation
        from ..models import Inspector

        variation_ids = ConfigurableVariation.objects.filter_multi_tenant(self.multi_tenant_company). \
            filter(parent=self.product, variation__active=True).values_list('variation_id', flat=True)

        if Inspector.objects.filter_multi_tenant(self.multi_tenant_company).filter(product_id__in=variation_ids, has_missing_information=True).exists():
            raise InspectorBlockFailed("Variations has missing information")


@InspectorBlockFactoryRegistry.register(DUPLICATE_VARIATIONS_ERROR)
class DuplicateVariationsInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(
            block,
            success_signal=inspector_duplicate_variations_success,
            failure_signal=inspector_duplicate_variations_failed,
            save_inspector=save_inspector
        )

    def _check(self):
        from products.models import ConfigurableVariation

        variation_ids = ConfigurableVariation.objects.filter_multi_tenant(self.multi_tenant_company).\
            filter(parent=self.product).values_list('variation_id', flat=True)

        if variation_ids.count() == 0:
            return

        unique_variations_cnt = self.product.get_unique_configurable_variations().count()
        if unique_variations_cnt == 0:
            return

        if self.product.configurable_variations.all().count() != unique_variations_cnt:
            raise InspectorBlockFailed("Product has duplicate variations with the same property combination.")


@InspectorBlockFactoryRegistry.register(NON_CONFIGURABLE_RULE_ERROR)
class NonConfigurableRuleInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(
            block,
            success_signal=inspector_non_configurable_rule_success,
            failure_signal=inspector_non_configurable_rule_failed,
            save_inspector=save_inspector
        )

    def _check(self):
        if not self.product.is_configurable():
            return

        configurator_properties_count = self.product.get_configurator_properties().count()

        if configurator_properties_count == 0:
            raise InspectorBlockFailed("Configurable product has no applicable configurator rules.")


@InspectorBlockFactoryRegistry.register(AMAZON_VALIDATION_ISSUES_ERROR)
class AmazonValidationIssuesInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(
            block,
            success_signal=inspector_amazon_validation_issues_success,
            failure_signal=inspector_amazon_validation_issues_failed,
            save_inspector=save_inspector,
        )

    def _check(self):
        from sales_channels.integrations.amazon.models import AmazonProductIssue

        if AmazonProductIssue.objects.filter_multi_tenant(self.multi_tenant_company).filter(
            remote_product__local_instance=self.product,
            is_validation_issue=True,
        ).exists():
            raise InspectorBlockFailed("Product has amazon validation issues.")


@InspectorBlockFactoryRegistry.register(AMAZON_REMOTE_ISSUES_ERROR)
class AmazonRemoteIssuesInspectorBlockFactory(InspectorBlockFactory):
    def __init__(self, block, save_inspector=True):
        super().__init__(
            block,
            success_signal=inspector_amazon_remote_issues_success,
            failure_signal=inspector_amazon_remote_issues_failed,
            save_inspector=save_inspector,
        )

    def _check(self):
        from sales_channels.integrations.amazon.models import AmazonProductIssue

        if AmazonProductIssue.objects.filter_multi_tenant(self.multi_tenant_company).filter(
            remote_product__local_instance=self.product,
            is_validation_issue=False,
        ).exists():
            raise InspectorBlockFailed("Product on amazon has remote issues.")
