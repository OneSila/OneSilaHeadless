from django.db import transaction
from django.db.models import Q
from products_inspector.constants import blocks, REQUIRED, OPTIONAL, NONE
from products_inspector.models import Inspector, InspectorBlock
from products.product_types import SIMPLE, BUNDLE, CONFIGURABLE, MANUFACTURABLE, DROPSHIP, SUPPLIER
import logging

from products_inspector.signals import inspector_missing_info_detected, inspector_missing_info_resolved, inspector_missing_optional_info_detected, \
    inspector_missing_optional_info_resolved

logger = logging.getLogger(__name__)


class SaveInspectorMixin:
    def save_inspector(self):
        applicability_fields = [
            'simple_product_applicability',
            'bundle_product_applicability',
            'configurable_product_applicability',
            'manufacturable_product_applicability',
            'dropship_product_applicability',
            'supplier_product_applicability',
        ]

        # Construct the Q object for required fields
        required_q = Q()
        for field in applicability_fields:
            required_q |= Q(**{f'{field}': REQUIRED})

        # Check for missing required information using OR across applicability fields
        has_required = self.inspector.blocks.filter(
            required_q,
            successfully_checked=False
        ).exists()

        # Construct the Q object for optional fields
        optional_q = Q()
        for field in applicability_fields:
            optional_q |= Q(**{f'{field}': OPTIONAL})

        # Check for missing optional information using OR across applicability fields
        has_optional = self.inspector.blocks.filter(
            optional_q,
            successfully_checked=False
        ).exists()

        previous_has_missing_info = self.inspector.has_missing_information
        previous_has_missing_optional_info = self.inspector.has_missing_optional_information

        self.inspector.has_missing_information = has_required
        self.inspector.has_missing_optional_information = has_optional
        self.inspector.save()

        # Handle transitions for has_missing_information
        if previous_has_missing_info != self.inspector.has_missing_information:
            if self.inspector.has_missing_information:
                inspector_missing_info_detected.send(sender=self.product.__class__, instance=self.product)
                logger.info(f"Signal inspector_missing_info_detected sent for product {self.product.sku}.")
            else:
                inspector_missing_info_resolved.send(sender=self.product.__class__, instance=self.product)
                logger.info(f"Signal inspector_missing_info_resolved sent for product {self.product.sku}.")

        # Handle transitions for has_missing_optional_information
        if previous_has_missing_optional_info != self.inspector.has_missing_optional_information:
            if self.inspector.has_missing_optional_information:
                inspector_missing_optional_info_detected.send(sender=self.product.__class__, instance=self.product)
                logger.info(f"Signal inspector_missing_optional_info_detected sent for product {self.product.sku}.")
            else:
                inspector_missing_optional_info_resolved.send(sender=self.product.__class__, instance=self.product)
                logger.info(f"Signal inspector_missing_optional_info_resolved sent for product {self.product.sku}.")


class ResyncInspectorFactory(SaveInspectorMixin):
    def __init__(self, inspector):
        self.inspector = inspector
        self.product = inspector.product
        self.blocks = self._get_ordered_blocks()

    def _get_ordered_blocks(self):
        """
        Retrieve all blocks for the inspector, ordered by sort_order.
        """
        return self.inspector.blocks.order_by('sort_order')

    def _sync_all_blocks(self):
        """
        Synchronize all blocks for the inspector.
        """
        for index, block in enumerate(self.blocks):
            self._sync_block(block)

    def _sync_block(self, block):
        from products_inspector.factories.inspector_block import InspectorBlockFactoryRegistry
        """
        Syncs a single block using the appropriate factory.
        """
        block_factory = InspectorBlockFactoryRegistry.get_factory(block.error_code)(
            block,
            save_inspector=False
        )
        block_factory.run()

    def run(self):
        """
        Run the full resync process for the inspector.
        """
        self._sync_all_blocks()
        self.save_inspector()


class InspectorCreateOrUpdateFactory(SaveInspectorMixin):
    def __init__(self, product, clear_blocks=False, run_sync=True):
        self.product = product
        self.clear_blocks = clear_blocks  # if clear blocks is true it will also check if the existent blocks should exist
        self.multi_tenant_company = product.multi_tenant_company
        self.run_sync = run_sync

    def _create_or_get_inspector(self):
        """
        Creates or gets an Inspector instance for the given product.
        """
        self.inspector, created = Inspector.objects.get_or_create(
            product=self.product,
            multi_tenant_company=self.multi_tenant_company
        )

        if created:
            logger.info(f"Created new Inspector for product {self.product.sku}")

    def _create_blocks(self):
        """
        Creates InspectorBlock instances based on the product type.
        """
        target_field_key = self._get_target_field_key()

        if not target_field_key:
            # If the product type doesn't match any target field, exit early
            return

        for block_config in blocks:
            target_field_value = block_config.get(target_field_key)
            if target_field_value and target_field_value != NONE:
                block_instance, created = InspectorBlock.objects.get_or_create(
                    inspector=self.inspector,
                    multi_tenant_company=self.multi_tenant_company,
                    **block_config
                )

                if created:
                    self._sync_block(block_instance)

    def _get_target_field_key(self):
        """
        Determines the appropriate target field key based on the product type.
        """
        product_type_map = {
            SIMPLE: 'simple_product_applicability',
            BUNDLE: 'bundle_product_applicability',
            CONFIGURABLE: 'configurable_product_applicability',
            MANUFACTURABLE: 'manufacturable_product_applicability',
            DROPSHIP: 'dropship_product_applicability',
            SUPPLIER: 'supplier_product_applicability',
        }
        return product_type_map.get(self.product.type)

    def _clear_blocks(self):

        if not self.clear_blocks:
            return

        target_field_key = self._get_target_field_key()

        if not target_field_key:
            # If the product type doesn't match any target field, exit early
            return

        for block in self.inspector.blocks.all().iterator():
            # Find the block configuration that matches the current block's error code (we removed the error code)
            block_config = next((config for config in blocks if config['error_code'] == block.error_code), None)

            if not block_config:
                # If no block config matches, this block is obsolete
                logger.info(f"Deleting obsolete InspectorBlock (error_code={block.error_code}) for product {self.product.sku}")
                block.delete()
                continue

            target_field_value = block_config.get(target_field_key)

            if not target_field_value or target_field_value == NONE:
                # If the block's target field value is NONE or not set, delete the block
                logger.info(f"Deleting unused InspectorBlock (error_code={block.error_code}) for product {self.product.sku}")
                block.delete()

    def _sync_block(self, block):
        from products_inspector.flows.inspector_block import inspector_block_sync_flow

        if not self.run_sync:
            return

        inspector_block_sync_flow(block)

    @transaction.atomic
    def run(self):
        """
        The main method that creates the inspector and its blocks.
        """
        self._create_or_get_inspector()
        self._create_blocks()
        self._clear_blocks()
        self.save_inspector()
