from django.utils.translation import gettext_lazy as _

from properties.models import Property


EBAY_INTERNAL_PROPERTY_DEFAULTS = [
    {
        'code': 'condition',
        'name': _("Condition"),
        'type': Property.TYPES.SELECT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__dimensions__length',
        'name': _("Package Length"),
        'type': Property.TYPES.FLOAT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__dimensions__width',
        'name': _("Package Width"),
        'type': Property.TYPES.FLOAT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__dimensions__height',
        'name': _("Package Height"),
        'type': Property.TYPES.FLOAT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__weight__value',
        'name': _("Package Weight"),
        'type': Property.TYPES.FLOAT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__packageType',
        'name': _("eBay Package Type"),
        'type': Property.TYPES.SELECT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__shippingIrregular',
        'name': _("Package Shipping Irregular"),
        'type': Property.TYPES.BOOLEAN,
        'is_root': True,
    },
    {
        'code': 'isbn',
        'name': _("International Standard Book Number"),
        'type': Property.TYPES.TEXT,
        'is_root': False,
    },
    {
        'code': 'brand',
        'name': _("Brand"),
        'type': Property.TYPES.SELECT,
        'is_root': False,
    },
    {
        'code': 'epid',
        'name': _("eBay Product ID"),
        'type': Property.TYPES.TEXT,
        'is_root': False,
    },
    {
        'code': 'mpn',
        'name': _("Manufacturer Part Number"),
        'type': Property.TYPES.TEXT,
        'is_root': False,
    },
    {
        'code': 'upc',
        'name': _("Universal Product Code"),
        'type': Property.TYPES.TEXT,
        'is_root': False,
    },
]

LENGTH_UNIT_CHOICES = [
    ("INCH", _("Inch")),
    ("FEET", _("Feet")),
    ("CENTIMETER", _("Centimeter")),
    ("METER", _("Meter")),
]

WEIGHT_UNIT_CHOICES = [
    ("POUND", _("Pound")),
    ("KILOGRAM", _("Kilogram")),
    ("OUNCE", _("Ounce")),
    ("GRAM", _("Gram")),
]
