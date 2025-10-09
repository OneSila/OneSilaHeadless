from django.utils.translation import gettext_lazy as _

from properties.models import Property


EBAY_CONDITION_OPTIONS = [
    {
        "value": "NEW",
        "label": _("New"),
        "description": _(
            "Brand-new, unopened item in its original packaging."
        ),
    },
    {
        "value": "LIKE_NEW",
        "label": _("Like New"),
        "description": _(
            "Item has been opened but shows virtually no signs of use."
        ),
    },
    {
        "value": "NEW_OTHER",
        "label": _("New (Other)"),
        "description": _(
            "New, unused item that may be missing original packaging or not sealed."
        ),
    },
    {
        "value": "NEW_WITH_DEFECTS",
        "label": _("New with Defects"),
        "description": _(
            "New, unused item with defects; typically apparel with minor imperfections."
        ),
    },
    {
        "value": "CERTIFIED_REFURBISHED",
        "label": _("Certified Refurbished"),
        "description": _(
            "Inspected, cleaned, and refurbished by the manufacturer or an approved vendor."
        ),
    },
    {
        "value": "EXCELLENT_REFURBISHED",
        "label": _("Excellent Refurbished"),
        "description": _(
            "Like-new condition refurbished by the manufacturer or an approved vendor."
        ),
    },
    {
        "value": "VERY_GOOD_REFURBISHED",
        "label": _("Very Good Refurbished"),
        "description": _(
            "Minimal wear; refurbished by the manufacturer or an approved vendor."
        ),
    },
    {
        "value": "GOOD_REFURBISHED",
        "label": _("Good Refurbished"),
        "description": _(
            "Moderate wear; refurbished by the manufacturer or an approved vendor."
        ),
    },
    {
        "value": "SELLER_REFURBISHED",
        "label": _("Seller Refurbished"),
        "description": _(
            "Restored to working order by the seller or a third party."
        ),
    },
    {
        "value": "USED_EXCELLENT",
        "label": _("Used - Excellent"),
        "description": _(
            "Used item in excellent condition with minimal wear."
        ),
    },
    {
        "value": "USED_VERY_GOOD",
        "label": _("Used - Very Good"),
        "description": _(
            "Used item in very good condition with minor signs of wear."
        ),
    },
    {
        "value": "USED_GOOD",
        "label": _("Used - Good"),
        "description": _(
            "Used item in good condition with moderate signs of wear."
        ),
    },
    {
        "value": "USED_ACCEPTABLE",
        "label": _("Used - Acceptable"),
        "description": _(
            "Used item in acceptable condition with noticeable signs of wear."
        ),
    },
    {
        "value": "FOR_PARTS_OR_NOT_WORKING",
        "label": _("For Parts or Not Working"),
        "description": _(
            "Item is non-functional or intended to be used for parts."
        ),
    },
    {
        "value": "PRE_OWNED_EXCELLENT",
        "label": _("Pre-owned - Excellent"),
        "description": _(
            "Previously owned apparel item in excellent condition with little to no wear."
        ),
    },
    {
        "value": "PRE_OWNED_FAIR",
        "label": _("Pre-owned - Fair"),
        "description": _(
            "Previously owned apparel item with noticeable wear or flaws."
        ),
    },
]


EBAY_PACKAGE_TYPE_OPTIONS = [
    {"value": "LETTER", "label": _("Letter")},
    {"value": "BULKY_GOODS", "label": _("Bulky Goods")},
    {"value": "CARAVAN", "label": _("Caravan")},
    {"value": "CARS", "label": _("Cars")},
    {"value": "EUROPALLET", "label": _("Euro Pallet")},
    {"value": "EXPANDABLE_TOUGH_BAGS", "label": _("Expandable Tough Bag")},
    {"value": "EXTRA_LARGE_PACK", "label": _("Extra Large Pack")},
    {"value": "FURNITURE", "label": _("Furniture")},
    {"value": "INDUSTRY_VEHICLES", "label": _("Industry Vehicle")},
    {"value": "LARGE_CANADA_POSTBOX", "label": _("Large Canada Post Box")},
    {"value": "LARGE_CANADA_POST_BUBBLE_MAILER", "label": _("Large Canada Post Bubble Mailer")},
    {"value": "LARGE_ENVELOPE", "label": _("Large Envelope")},
    {"value": "MAILING_BOX", "label": _("Mailing Box")},
    {"value": "MEDIUM_CANADA_POST_BOX", "label": _("Medium Canada Post Box")},
    {"value": "MEDIUM_CANADA_POST_BUBBLE_MAILER", "label": _("Medium Canada Post Bubble Mailer")},
    {"value": "MOTORBIKES", "label": _("Motorbike")},
    {"value": "ONE_WAY_PALLET", "label": _("One-way Pallet")},
    {"value": "PACKAGE_THICK_ENVELOPE", "label": _("Thick Envelope")},
    {"value": "PADDED_BAGS", "label": _("Padded Bag")},
    {"value": "PARCEL_OR_PADDED_ENVELOPE", "label": _("Parcel or Padded Envelope")},
    {"value": "ROLL", "label": _("Roll")},
    {"value": "SMALL_CANADA_POST_BOX", "label": _("Small Canada Post Box")},
    {"value": "SMALL_CANADA_POST_BUBBLE_MAILER", "label": _("Small Canada Post Bubble Mailer")},
    {"value": "TOUGH_BAGS", "label": _("Tough Bag")},
    {"value": "UPS_LETTER", "label": _("UPS Letter")},
    {"value": "USPS_FLAT_RATE_ENVELOPE", "label": _("USPS Flat-rate Envelope")},
    {"value": "USPS_LARGE_PACK", "label": _("USPS Large Pack")},
    {"value": "VERY_LARGE_PACK", "label": _("Very Large Pack")},
    {"value": "WINE_PAK", "label": _("Wine Pak")},
]


EBAY_INTERNAL_PROPERTY_DEFAULTS = [
    {
        'code': 'condition',
        'name': _("Condition"),
        'type': Property.TYPES.SELECT,
        'is_root': True,
        'options': EBAY_CONDITION_OPTIONS,
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
        'options': EBAY_PACKAGE_TYPE_OPTIONS,
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
        'code': 'epid',
        'name': _("eBay Product ID"),
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
