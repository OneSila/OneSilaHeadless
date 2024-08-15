from core import models
from products.models import Product
from django.utils.translation import gettext_lazy as _
from products_inspector.managers import InspectorBlockHasImagesManager, InspectorBlockMissingPricesManager, InactivePiecesInspectorBlockManager, \
    MissingVariationInspectorBlockManager, MissingBundleItemsInspectorBlockManager, MissingBillOfMaterialsInspectorBlockManager, \
    MissingSupplierProductsInspectorBlockManager, InactiveBundleItemsInspectorBlockManager, MissingEanCodeInspectorBlockManager, \
    MissingProductTypeInspectorBlockManager, MissingRequiredPropertiesInspectorBlockManager, MissingOptionalPropertiesInspectorBlockManager, \
    MissingSupplierPricesManager, MissingStockManager, MissingLeadTimeManager, MissingManualPriceListOverrideManager, VariationMismatchProductTypeManager, \
    ItemsMismatchProductTypeManager, BomMismatchProductTypeManager, ItemsMissingMandatoryInformationManager, VariationsMissingMandatoryInformationManager, \
    BomMissingMandatoryInformationManager, DuplicateVariationsManager, NonConfigurableRuleInspectorBlockManager


class Inspector(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inspector')
    has_missing_information = models.BooleanField(default=True)
    has_missing_optional_information = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['product']),
        ]

    def inspect_product(self, run_async=False):
        from products_inspector.flows.inspector import resync_inspector_flow
        resync_inspector_flow(self, run_async)

    def __str__(self):
        return f"Inspector for {self.product.sku}"

class InspectorBlock(models.Model):
    from products_inspector.constants import ERROR_TYPES, MANDATORY_TYPE_CHOICES, NONE


    inspector = models.ForeignKey('Inspector', on_delete=models.CASCADE, related_name='blocks')
    # maybe in the full resync we will want to controll the order
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_('Sort Order'))

    # Fields indicating the product types the block applies to
    simple_product_applicability = models.CharField(max_length=10, choices=MANDATORY_TYPE_CHOICES, default=NONE)
    configurable_product_applicability = models.CharField(max_length=10, choices=MANDATORY_TYPE_CHOICES, default=NONE)
    manufacturable_product_applicability = models.CharField(max_length=10, choices=MANDATORY_TYPE_CHOICES, default=NONE)
    bundle_product_applicability = models.CharField(max_length=10, choices=MANDATORY_TYPE_CHOICES, default=NONE)
    dropship_product_applicability = models.CharField(max_length=10, choices=MANDATORY_TYPE_CHOICES, default=NONE)
    supplier_product_applicability = models.CharField(max_length=10, choices=MANDATORY_TYPE_CHOICES, default=NONE)

    # Store the error code here
    error_code = models.IntegerField(choices=ERROR_TYPES)

    # Reflects if the block passed its check
    successfully_checked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("inspector", "error_code")
        indexes = [
            models.Index(fields=['inspector']),
        ]

    def get_target_field_key(self):
        from products.product_types import SIMPLE, BUNDLE, UMBRELLA, MANUFACTURABLE, DROPSHIP, SUPPLIER
        """
        Determines the appropriate target field key based on the associated product's type.
        """
        product_type_map = {
            SIMPLE: 'simple_product_applicability',
            BUNDLE: 'bundle_product_applicability',
            UMBRELLA: 'configurable_product_applicability',
            MANUFACTURABLE: 'manufacturable_product_applicability',
            DROPSHIP: 'dropship_product_applicability',
            SUPPLIER: 'supplier_product_applicability',
        }
        return product_type_map.get(self.inspector.product.type)

    def __str__(self):
        return f"{self.get_error_code_display()} for {self.inspector.product.sku} ({self.successfully_checked})"

class InspectorBlockHasImages(InspectorBlock):
    from .constants import has_image_block

    objects = InspectorBlockHasImagesManager()
    proxy_filter_fields = has_image_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Has Images")

class InspectorBlockMissingPrices(InspectorBlock):
    from .constants import missing_prices_block

    objects = InspectorBlockMissingPricesManager()
    proxy_filter_fields = missing_prices_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Prices")


class InspectorBlockInactivePieces(InspectorBlock):
    from .constants import inactive_pieces_block

    objects = InactivePiecesInspectorBlockManager()
    proxy_filter_fields = inactive_pieces_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Inactive Pieces")


class InspectorBlockInactiveBundleItems(InspectorBlock):
    from .constants import inactive_bundle_items_block

    objects = InactiveBundleItemsInspectorBlockManager()
    proxy_filter_fields = inactive_bundle_items_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Inactive Bundle Items")

class InspectorBlockMissingVariation(InspectorBlock):
    from .constants import missing_variation_block

    objects = MissingVariationInspectorBlockManager()
    proxy_filter_fields = missing_variation_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Variations")


class InspectorBlockMissingBundleItems(InspectorBlock):
    from .constants import missing_bundle_items_block

    objects = MissingBundleItemsInspectorBlockManager()
    proxy_filter_fields = missing_bundle_items_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Bundle Items")


class InspectorBlockMissingBillOfMaterials(InspectorBlock):
    from .constants import missing_bill_of_materials_block

    objects = MissingBillOfMaterialsInspectorBlockManager()
    proxy_filter_fields = missing_bill_of_materials_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Bill of Materials")


class InspectorBlockMissingSupplierProducts(InspectorBlock):
    from .constants import missing_supplier_products_block

    objects = MissingSupplierProductsInspectorBlockManager()
    proxy_filter_fields = missing_supplier_products_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Supplier Products")


class MissingEanCodeInspectorBlock(InspectorBlock):
    from .constants import missing_ean_code_block

    objects = MissingEanCodeInspectorBlockManager()
    proxy_filter_fields = missing_ean_code_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing EAN Code")


class MissingProductTypeInspectorBlock(InspectorBlock):
    from .constants import missing_product_type_block

    objects = MissingProductTypeInspectorBlockManager()
    proxy_filter_fields = missing_product_type_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Product Type")

class MissingRequiredPropertiesInspectorBlock(InspectorBlock):
    from .constants import missing_required_properties_block

    objects = MissingRequiredPropertiesInspectorBlockManager()
    proxy_filter_fields = missing_required_properties_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Required Properties")

class MissingOptionalPropertiesInspectorBlock(InspectorBlock):
    from .constants import missing_optional_properties_block

    objects = MissingOptionalPropertiesInspectorBlockManager()
    proxy_filter_fields = missing_optional_properties_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Optional Properties")


class MissingSupplierPricesInspectorBlock(InspectorBlock):
    from .constants import missing_supplier_prices_block

    objects = MissingSupplierPricesManager()
    proxy_filter_fields = missing_supplier_prices_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Supplier Prices")


class MissingStockInspectorBlock(InspectorBlock):
    from .constants import missing_stock_block

    objects = MissingStockManager()
    proxy_filter_fields = missing_stock_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Stock")


class MissingLeadTimeInspectorBlock(InspectorBlock):
    from .constants import missing_lead_time_block

    objects = MissingLeadTimeManager()
    proxy_filter_fields = missing_lead_time_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Lead Time")


class MissingManualPriceListOverrideInspectorBlock(InspectorBlock):
    from .constants import missing_manual_pricelist_override_block

    objects = MissingManualPriceListOverrideManager()
    proxy_filter_fields = missing_manual_pricelist_override_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Missing Manual Price List Override")


class VariationMismatchProductTypeInspectorBlock(InspectorBlock):
    from .constants import variation_mismatch_product_type_block

    objects = VariationMismatchProductTypeManager()
    proxy_filter_fields = variation_mismatch_product_type_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Variation Mismatch Product Type")


class ItemsMismatchProductTypeInspectorBlock(InspectorBlock):
    from .constants import items_mismatch_product_type_block

    objects = ItemsMismatchProductTypeManager()
    proxy_filter_fields = items_mismatch_product_type_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Items Mismatch Product Type")


class BomMismatchProductTypeInspectorBlock(InspectorBlock):
    from .constants import bom_mismatch_product_type_block

    objects = BomMismatchProductTypeManager()
    proxy_filter_fields = bom_mismatch_product_type_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block BOM Mismatch Product Type")


class ItemsMissingMandatoryInformationInspectorBlock(InspectorBlock):
    from .constants import items_missing_mandatory_information_block

    objects = ItemsMissingMandatoryInformationManager()
    proxy_filter_fields = items_missing_mandatory_information_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Items Missing Mandatory Information")


class VariationsMissingMandatoryInformationInspectorBlock(InspectorBlock):
    from .constants import variations_missing_mandatory_information_block

    objects = VariationsMissingMandatoryInformationManager()
    proxy_filter_fields = variations_missing_mandatory_information_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Variations Missing Mandatory Information")


class BomMissingMandatoryInformationInspectorBlock(InspectorBlock):
    from .constants import bom_missing_mandatory_information_block

    objects = BomMissingMandatoryInformationManager()
    proxy_filter_fields = bom_missing_mandatory_information_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block BOM Missing Mandatory Information")

class DuplicateVariationsInspectorBlock(InspectorBlock):
    from .constants import duplicate_variations_block

    objects = DuplicateVariationsManager()
    proxy_filter_fields = duplicate_variations_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Duplicate Variations")


class NonConfigurableRuleInspectorBlock(InspectorBlock):
    from .constants import non_configurable_rule_block

    objects = NonConfigurableRuleInspectorBlockManager()
    proxy_filter_fields = non_configurable_rule_block

    class Meta:
        proxy = True
        verbose_name = _("Inspector Block Non-Configurable Rule")
