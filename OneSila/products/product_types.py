from django.utils.translation import gettext_lazy as _

SIMPLE = 'SIMPLE'
BUNDLE = 'BUNDLE'
UMBRELLA = 'UMBRELLA'
CONFIGURABLE = 'CONFIGURABLE'
ALIAS = 'ALIAS'

PRODUCT_TYPE_CHOICES = (
    (BUNDLE, _('Bundle Product')),
    (CONFIGURABLE, _('Configurable Product')),
    (SIMPLE, _('Simple Product')),
    (ALIAS, _('Alias Product')),
)

HAS_PRICES_TYPES = [
    SIMPLE,
    BUNDLE,
    ALIAS
]


HAS_DIRECT_INVENTORY_TYPES = [
]

HAS_INDIRECT_INVENTORY_TYPES = [
    SIMPLE,
]
