from core.managers import QuerySet, Manager, MultiTenantCompanyCreateMixin, \
    QuerySetProxyModelMixin, MultiTenantQuerySet, MultiTenantManager


class ProductQuerySet(MultiTenantQuerySet):
    def filter_configurable(self):
        return self.filter(type=self.model.UMBRELLA)

    def filter_variation(self):
        return self.filter(type=self.model.SIMPLE)

    def filter_bundle(self):
        return self.filter(type=self.model.BUNDLE)

    def filter_manufacturer(self):
        return self.filter(type=self.model.MANUFACTURER)

    def filter_dropship(self):
        return self.filter(type=self.model.DROPSHIP)

    def filter_has_prices(self):
        return self.filter(type__in=self.model.HAS_PRICES_TYPES)

    def filter_by_properties_rule(self, rule):
        from properties.models import ProductProperty
        product_ids = ProductProperty.objects.filter(value_select=rule.product_type).values_list('product_id', flat=True)
        return self.filter_multi_tenant(multi_tenant_company=rule.multi_tenant_company).filter(id__in=product_ids)


class ProductManager(MultiTenantManager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def filter_by_properties_rule(self, rule):
        return self.get_queryset().filter_by_properties_rule(rule)


class ConfigurableQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class ConfigurableManager(ProductManager):
    def get_queryset(self):
        return ConfigurableQuerySet(self.model, using=self._db)


class VariationQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class VariationManager(ProductManager):
    def get_queryset(self):
        return VariationQuerySet(self.model, using=self._db)


class BundleQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    def get_all_item_products(self, product):
        from .models import Product, BundleVariation, BillOfMaterial

        """
        Recursively fetch all products that are part of the BOM of the given manufacturable product.
        Returns a QuerySet of all BOM components.
        """

        def fetch_items_components(product, collected_ids=None):
            if collected_ids is None:
                collected_ids = set()

            # Get direct BundleVariation components
            direct_components = BundleVariation.objects.filter(umbrella=product).values_list('variation_id', flat=True)
            new_ids = set(direct_components) - collected_ids

            # Get direct BillOfMaterial components for manufacturable products
            if product.is_manufacturable():
                bom_components = BillOfMaterial.objects.filter(umbrella=product).values_list('variation_id', flat=True)
                new_ids.update(set(bom_components) - collected_ids)

            if not new_ids:
                return collected_ids

            collected_ids.update(new_ids)

            # Recursively fetch components for each new variation
            for variation_id in new_ids:
                variation = Product.objects.get(id=variation_id)
                if variation.is_bundle() or variation.is_manufacturable():
                    fetch_items_components(variation, collected_ids)

            return collected_ids

        # Fetch all components
        all_items_component_ids = fetch_items_components(product)

        # Return a QuerySet of all the components
        return Product.objects.filter(id__in=all_items_component_ids)


class BundleManager(ProductManager):
    def get_queryset(self):
        return BundleQuerySet(self.model, using=self._db)

    def get_all_item_products(self, product):
        return self.get_queryset().get_all_item_products(product)


class ManufacturableQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    def get_all_bills_of_materials_products(self, product):
        from .models import Product, BillOfMaterial
        """
        Recursively fetch all products that are part of the BOM of the given manufacturable product.
        Returns a QuerySet of all BOM components.
        """
        def fetch_bom_components(product, collected_ids=None):
            if collected_ids is None:
                collected_ids = set()

            # Get direct BOM components
            direct_components = BillOfMaterial.objects.filter(umbrella=product).values_list('variation_id', flat=True)
            new_ids = set(direct_components) - collected_ids

            if not new_ids:
                return collected_ids

            collected_ids.update(new_ids)

            # Recursively fetch BOM components for each new variation
            for variation_id in new_ids:
                variation = Product.objects.get(id=variation_id)
                if variation.is_manufacturable():
                    fetch_bom_components(variation, collected_ids)

            return collected_ids

        # Fetch all BOM components
        all_bom_component_ids = fetch_bom_components(product)

        # Return a QuerySet of all the BOM components
        return Product.objects.filter(id__in=all_bom_component_ids)


class ManufacturableManager(ProductManager):
    def get_queryset(self):
        return ManufacturableQuerySet(self.model, using=self._db)

    def get_all_bills_of_materials_products(self, product):
        return self.get_queryset().get_all_bills_of_materials_products(product)


class DropshipQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class DropshipManager(ProductManager):
    def get_queryset(self):
        return DropshipQuerySet(self.model, using=self._db)


class SupplierProductQuerySet(QuerySetProxyModelMixin, ProductQuerySet):
    pass


class SupplierProductManager(ProductManager):
    def get_queryset(self):
        return SupplierProductQuerySet(self.model, using=self._db)
