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


class MissingStockQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class MissingStockManager(InspectorBlockManager):
    def get_queryset(self):
        return MissingStockQuerySet(self.model, using=self._db)


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


class AmazonValidationIssuesQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class AmazonValidationIssuesInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return AmazonValidationIssuesQuerySet(self.model, using=self._db)


class AmazonRemoteIssuesQuerySet(QuerySetProxyModelMixin, InspectorBlockQuerySet):
    pass


class AmazonRemoteIssuesInspectorBlockManager(InspectorBlockManager):
    def get_queryset(self):
        return AmazonRemoteIssuesQuerySet(self.model, using=self._db)
