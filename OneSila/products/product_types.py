from django.utils.translation import gettext_lazy as _

SIMPLE = 'SIMPLE'
BUNDLE = 'BUNDLE'
UMBRELLA = 'UMBRELLA'
CONFIGURABLE = 'CONFIGURABLE'
MANUFACTURABLE = 'MANUFACTURABLE'
DROPSHIP = 'DROPSHIP'
SUPPLIER = 'SUPPLIER'

PRODUCT_TYPE_CHOICES = (
    (BUNDLE, _('Bundle Product')),
    (CONFIGURABLE, _('Configurable Product')),
    (MANUFACTURABLE, _('Manufacturable Product')),
    (DROPSHIP, _('Dropship Product')),
    (SUPPLIER, _('Supplier Product')),
    (SIMPLE, _('Simple Product')),
)

HAS_PRICES_TYPES = [
    SIMPLE,
    BUNDLE,
    MANUFACTURABLE,
    DROPSHIP
]


HAS_DIRECT_INVENTORY_TYPES = [
    SUPPLIER,
    MANUFACTURABLE,
]

HAS_INDIRECT_INVENTORY_TYPES = [
    SIMPLE,
    DROPSHIP
]
