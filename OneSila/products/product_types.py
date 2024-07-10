from django.utils.translation import gettext_lazy as _

SIMPLE = 'SIMPLE'
BUNDLE = 'BUNDLE'
UMBRELLA = 'UMBRELLA'
MANUFACTURABLE = 'MANUFACTURABLE'
DROPSHIP = 'DROPSHIP'
SUPPLIER = 'SUPPLIER'

PRODUCT_TYPE_CHOICES = (
    (BUNDLE, _('Bundle Product')),
    (UMBRELLA, _('Umbrella Product')),
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
