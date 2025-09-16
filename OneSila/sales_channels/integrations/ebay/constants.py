from django.utils.translation import gettext_lazy as _

from properties.models import Property


EBAY_INTERNAL_PROPERTY_DEFAULTS = [
    {
        'code': 'condition',
        'label': _("Condition"),
        'type': Property.TYPES.SELECT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__dimensions__length',
        'label': _("Package Length"),
        'type': Property.TYPES.FLOAT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__dimensions__width',
        'label': _("Package Width"),
        'type': Property.TYPES.FLOAT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__dimensions__height',
        'label': _("Package Height"),
        'type': Property.TYPES.FLOAT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__weight__value',
        'label': _("Package Weight"),
        'type': Property.TYPES.FLOAT,
        'is_root': True,
    },
    {
        'code': 'packageWeightAndSize__packageType',
        'label': _("eBay Package Type"),
        'type': Property.TYPES.SELECT,
        'is_root': True,
    },
    {
        'code': 'isbn',
        'label': _("International Standard Book Number"),
        'type': Property.TYPES.TEXT,
        'is_root': False,
    },
    {
        'code': 'brand',
        'label': _("Brand"),
        'type': Property.TYPES.SELECT,
        'is_root': False,
    },
    {
        'code': 'mpn',
        'label': _("Manufacturer Part Number"),
        'type': Property.TYPES.TEXT,
        'is_root': False,
    },
    {
        'code': 'upc',
        'label': _("Universal Product Code"),
        'type': Property.TYPES.TEXT,
        'is_root': False,
    },
]


def default_length_unit_choices():
    return [
        {"value": "INCH", "label": _("Inch")},
        {"value": "FEET", "label": _("Feet")},
        {"value": "CENTIMETER", "label": _("Centimeter")},
        {"value": "METER", "label": _("Meter")},
    ]


def default_weight_unit_choices():
    return [
        {"value": "POUND", "label": _("Pound")},
        {"value": "KILOGRAM", "label": _("Kilogram")},
        {"value": "OUNCE", "label": _("Ounce")},
        {"value": "GRAM", "label": _("Gram")},
    ]
