from accounting.factories.local_instance.mixins import DocumentCreateFactoryMixin
from accounting.models.local_instance import CreditNote, CreditNoteItem
from accounting.signals import create_remote_credit_note


class GenerateCreditNoteFileFactory:
    def __init__(self, document):
        self.document = document

    def run(self):
        pass

class CreditNoteCreateFactory(DocumentCreateFactoryMixin):
    local_class = CreditNote
    local_item_class = CreditNoteItem
    field_map = {
        'received_on': 'document_date',
        'order__customer__name': 'customer_name',
        'order__invoice_address__full_address': 'customer_invoice_address',
        'order__shipping_address__full_address': 'customer_shipping_address',
        'order__customer__email': 'customer_email',
        'order__customer__phone': 'customer_phone',
        'order__invoice_address__vat_number': 'customer_vat_number',
        'order__currency__symbol': 'currency_symbol',
        'order__price_incl_vat': 'price_incl_vat',
        'order__reference': 'order_number',
    }
    item_field_map = {
        'quantity': 'quantity',
        'order_item__price': 'unit_price',
        'order_item__product__vat_rate': 'vat_rate',
        'order_item__product__vat_rate__rate': 'preserved_vat_rate',
    }
    internal_company_map = 'order__internal_company'
    get_items_method = 'orderreturnitem_set'
    generate_document_factory = GenerateCreditNoteFileFactory
    signal_to_trigger = create_remote_credit_note
