from core.managers import MultiTenantQuerySet, MultiTenantManager, QuerySetProxyModelMixin


class InspectorBlockQuerySet(MultiTenantQuerySet):
    def filter_required_simple(self):
        return self.filter(simple_product_applicability=self.model.REQUIRED)

    def filter_required_configurable(self):
        return self.filter(configurable_product_applicability=self.model.REQUIRED)

    def filter_required_manufacturable(self):
        return self.filter(manufacturable_product_applicability=self.model.REQUIRED)

    def filter_required_bundle(self):
        return self.filter(bundle_product_applicability=self.model.REQUIRED)

    def filter_required_dropship(self):
        return self.filter(dropship_product_applicability=self.model.REQUIRED)

    def filter_required_supplier(self):
        return self.filter(supplier_product_applicability=self.model.REQUIRED)


class InspectorBlockManager(MultiTenantManager):
    def get_queryset(self):
        return InspectorBlockQuerySet(self.model, using=self._db)


class InspectorBlockHasImagesQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class InspectorBlockHasImagesManager(InspectorBlockManager):
    def get_queryset(self):
        return InspectorBlockHasImagesQuerySet(self.model, using=self._db)


class InspectorBlockMissingPricesQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class InspectorBlockMissingPricesManager(InspectorBlockManager):
    def get_queryset(self):
        return InspectorBlockMissingPricesQuerySet(self.model, using=self._db)


class InactivePiecesInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class InactivePiecesInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return InactivePiecesInspectorBlockQuerySet(self.model, using=self._db)


class MissingVariationInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingVariationInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingVariationInspectorBlockQuerySet(self.model, using=self._db)


class MissingBundleItemsInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingBundleItemsInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingBundleItemsInspectorBlockQuerySet(self.model, using=self._db)


class MissingBillOfMaterialsInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingBillOfMaterialsInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingBillOfMaterialsInspectorBlockQuerySet(self.model, using=self._db)


class MissingSupplierProductsInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingSupplierProductsInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingSupplierProductsInspectorBlockQuerySet(self.model, using=self._db)


class InactiveBundleItemsInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class InactiveBundleItemsInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return InactiveBundleItemsInspectorBlockQuerySet(self.model, using=self._db)


class MissingEanCodeInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingEanCodeInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingEanCodeInspectorBlockQuerySet(self.model, using=self._db)


class MissingProductTypeInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingProductTypeInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingProductTypeInspectorBlockQuerySet(self.model, using=self._db)


class MissingRequiredPropertiesInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingRequiredPropertiesInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingRequiredPropertiesInspectorBlockQuerySet(self.model, using=self._db)


class MissingOptionalPropertiesInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingOptionalPropertiesInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingOptionalPropertiesInspectorBlockQuerySet(self.model, using=self._db)


class MissingSupplierPricesQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingSupplierPricesManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingSupplierPricesQuerySet(self.model, using=self._db)


class MissingStockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingStockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingStockQuerySet(self.model, using=self._db)


class MissingLeadTimeQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingLeadTimeManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingLeadTimeQuerySet(self.model, using=self._db)


class MissingManualPriceListOverrideQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingManualPriceListOverrideManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingManualPriceListOverrideQuerySet(self.model, using=self._db)


class VariationMismatchProductTypeQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class VariationMismatchProductTypeManager(InspectorBlockManager):
    def get_queryset(self):
        return VariationMismatchProductTypeQuerySet(self.model, using=self._db)


class ItemsMismatchProductTypeQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class ItemsMismatchProductTypeManager(InspectorBlockManager):
    def get_queryset(self):
        return ItemsMismatchProductTypeQuerySet(self.model, using=self._db)


class BomMismatchProductTypeQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class BomMismatchProductTypeManager(InspectorBlockManager):
    def get_queryset(self):
        return BomMismatchProductTypeQuerySet(self.model, using=self._db)


class ItemsMissingMandatoryInformationQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class ItemsMissingMandatoryInformationManager(InspectorBlockManager):
    def get_queryset(self):
        return ItemsMissingMandatoryInformationQuerySet(self.model, using=self._db)


class VariationsMissingMandatoryInformationQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class VariationsMissingMandatoryInformationManager(InspectorBlockManager):
    def get_queryset(self):
        return VariationsMissingMandatoryInformationQuerySet(self.model, using=self._db)


class BomMissingMandatoryInformationQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class BomMissingMandatoryInformationManager(InspectorBlockManager):
    def get_queryset(self):
        return BomMissingMandatoryInformationQuerySet(self.model, using=self._db)


class DuplicateVariationsQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class DuplicateVariationsManager(InspectorBlockManager):
    def get_queryset(self):
        return DuplicateVariationsQuerySet(self.model, using=self._db)


class NonConfigurableRuleInspectorBlockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class NonConfigurableRuleInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return NonConfigurableRuleInspectorBlockQuerySet(self.model, using=self._db)
