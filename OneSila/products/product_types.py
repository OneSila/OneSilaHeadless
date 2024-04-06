from django.utils.translation import gettext_lazy as _

VARIATION = 'VARIATION'
BUNDLE = 'BUNDLE'
UMBRELLA = 'UMBRELLA'

PRODUCT_TYPE_CHOICES = (
    (VARIATION, _('Product Variation')),
    (BUNDLE, _('Bundle Product')),
    (UMBRELLA, _('Umbrella Product')),
)
