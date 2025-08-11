from core.helpers import get_nested_attr
from imports_exports.factories.mixins import AbstractImportInstance, ImportOperationMixin
from currencies.models import Currency
from sales_prices.models import SalesPriceList


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
