from core.helpers import get_nested_attr
from imports_exports.factories.mixins import AbstractImportInstance, ImportOperationMixin
from currencies.models import Currency
from core.signals import post_create
from sales_prices.models import SalesPriceList, SalesPriceListItem


class SalesPriceListImport(ImportOperationMixin):
    """Import operation for SalesPriceList."""
    get_identifiers = ['name', 'start_date', 'end_date', 'currency']

    def build_kwargs(self):
        """Build kwargs including None values for start and end dates."""
        kwargs = {'multi_tenant_company': self.multi_tenant_company}
        for identifier in self.get_identifiers:
            value = get_nested_attr(self.import_instance, identifier)
            if identifier in ['start_date', 'end_date']:
                # Include even if None to filter by NULL values
                kwargs[identifier] = value
            elif value is not None or identifier == 'sales_channel':
                kwargs[identifier] = value
        self.get_kwargs = kwargs
        self.get_translation_kwargs = kwargs


class SalesPriceListItemImport(ImportOperationMixin):
    """Import operation for SalesPriceListItem."""
    get_identifiers = ['salespricelist', 'product']


class ImportSalesPriceListInstance(AbstractImportInstance):
    """Import instance for SalesPriceList."""

    def __init__(self, data: dict, import_process=None, currency=None, instance=None):
        super().__init__(data, import_process, instance)
        self.currency = currency

        self.set_field_if_exists('currency_data')
        self.set_field_if_exists('name')
        self.set_field_if_exists('start_date')
        self.set_field_if_exists('end_date')
        self.set_field_if_exists('vat_included')
        self.set_field_if_exists('auto_update_prices')
        self.set_field_if_exists('auto_add_products')
        self.set_field_if_exists('price_change_pcnt')
        self.set_field_if_exists('discount_pcnt')
        self.set_field_if_exists('notes')
        self.set_field_if_exists('sales_pricelist_items')

        self.validate()
        self._set_currency()
        self.created = False

    @property
    def local_class(self):
        return SalesPriceList

    @property
    def updatable_fields(self):
        return [
            'vat_included',
            'auto_update_prices',
            'auto_add_products',
            'price_change_pcnt',
            'discount_pcnt',
            'notes',
        ]

    def validate(self):
        if self.instance:
            return

        if not hasattr(self, 'name'):
            raise ValueError("The 'name' field is required.")

        currency_data = getattr(self, 'currency_data', None)
        if not (self.currency or currency_data):
            raise ValueError("Either 'currency' or 'currency_data' must be provided.")

        if (
            hasattr(self, 'start_date')
            and hasattr(self, 'end_date')
            and self.start_date
            and self.end_date
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date cannot be after end_date.")

    def _set_currency(self):
        if self.currency:
            return

        if hasattr(self, 'currency_data'):
            self.currency, _ = Currency.objects.get_or_create(
                multi_tenant_company=self.multi_tenant_company,
                **self.currency_data,
            )
            return

        raise ValueError("There is no currency information provided.")

    def process_logic(self):
        fac = SalesPriceListImport(self, self.import_process, instance=self.instance)
        fac.run()
        self.instance = fac.instance
        self.created = fac.created

    def post_process_logic(self):
        if hasattr(self, 'sales_pricelist_items'):
            self.set_sales_pricelist_items()

    def set_sales_pricelist_items(self):
        item_ids = []
        for item in self.sales_pricelist_items:
            product = item.get('product') if isinstance(item, dict) else None
            import_instance = ImportSalesPriceListItemInstance(
                item,
                self.import_process,
                sales_pricelist=self.instance,
                product=product,
            )
            import_instance.process()
            if import_instance.instance is not None:
                item_ids.append(import_instance.instance.id)
        self.sales_pricelist_item_instances = SalesPriceListItem.objects.filter(id__in=item_ids)


class ImportSalesPriceListItemInstance(AbstractImportInstance):
    """Import instance for SalesPriceListItem."""

    def __init__(
        self,
        data: dict,
        import_process=None,
        sales_pricelist=None,
        product=None,
        instance=None,
        disable_auto_update=False,
    ):
        super().__init__(data, import_process, instance)
        self.salespricelist = sales_pricelist
        self.product = product

        self.set_field_if_exists('salespricelist')
        self.set_field_if_exists('salespricelist_data')
        self.set_field_if_exists('product')
        self.set_field_if_exists('product_data')
        self.set_field_if_exists('price_auto')
        self.set_field_if_exists('discount_auto')
        self.set_field_if_exists('price_override')
        self.set_field_if_exists('discount_override')
        self.set_field_if_exists('disable_auto_update', default_value=disable_auto_update)

        if not self.salespricelist:
            self.salespricelist = getattr(self, 'salespricelist', None)
        if not self.product:
            self.product = getattr(self, 'product', None)

        self._set_sales_pricelist_import_instance()
        self._set_product_import_instance()
        self.validate()
        self.created = False

    @property
    def local_class(self):
        return SalesPriceListItem

    @property
    def updatable_fields(self):
        return ['price_auto', 'discount_auto', 'price_override', 'discount_override']

    def validate(self):
        if self.instance:
            return

        if not (self.salespricelist or hasattr(self, 'salespricelist_data')):
            raise ValueError("Either 'sales_pricelist' or 'sales_pricelist_data' must be provided.")

        if not (self.product or hasattr(self, 'product_data')):
            raise ValueError("Either 'product' or 'product_data' must be provided.")

    def _set_sales_pricelist_import_instance(self):
        self.sales_pricelist_import_instance = None
        if not self.salespricelist and hasattr(self, 'salespricelist_data'):
            self.sales_pricelist_import_instance = ImportSalesPriceListInstance(
                self.salespricelist_data,
                self.import_process,
            )

    def _set_product_import_instance(self):
        from .products import ImportProductInstance

        self.product_import_instance = None
        if not self.product and hasattr(self, 'product_data'):
            self.product_import_instance = ImportProductInstance(self.product_data, self.import_process)

    def process_logic(self):
        if not self.salespricelist and self.sales_pricelist_import_instance:
            self.sales_pricelist_import_instance.process()
            self.salespricelist = self.sales_pricelist_import_instance.instance

        if not self.product and self.product_import_instance:
            self.product_import_instance.process()
            self.product = self.product_import_instance.instance

        fac = SalesPriceListItemImport(self, self.import_process, instance=self.instance)

        if self.disable_auto_update:
            from sales_prices.receivers import salespricelistitem__salespricelist__post_create

            post_create.disconnect(
                salespricelistitem__salespricelist__post_create,
                sender=SalesPriceListItem,
            )

        try:
            fac.run()
        finally:
            if self.disable_auto_update:
                from sales_prices.receivers import salespricelistitem__salespricelist__post_create

                post_create.connect(
                    salespricelistitem__salespricelist__post_create,
                    sender=SalesPriceListItem,
                )

        self.instance = fac.instance
        self.created = fac.created
