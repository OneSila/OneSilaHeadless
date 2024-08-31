from django.utils.translation import gettext_lazy as _

# APPLICABILITY SECTION
REQUIRED = 'REQUIRED'
OPTIONAL = 'OPTIONAL'
NONE = 'NONE'

MANDATORY_TYPE_CHOICES = (
    (REQUIRED, _('Required')),
    (OPTIONAL, _('Optional')),
    (NONE, _('None')),
)

# ERROR CODES SECTION
HAS_IMAGES_ERROR = 101
MISSING_PRICES_ERROR = 102
INACTIVE_BILL_OF_MATERIALS_ERROR = 103
INACTIVE_BUNDLE_ITEMS_ERROR = 104
MISSING_VARIATION_ERROR = 105
MISSING_BUNDLE_ITEMS_ERROR = 106
MISSING_BILL_OF_MATERIALS_ERROR = 107
MISSING_SUPPLIER_PRODUCTS_ERROR = 108
MISSING_EAN_CODE_ERROR = 109
MISSING_PRODUCT_TYPE_ERROR = 110
MISSING_REQUIRED_PROPERTIES_ERROR = 111
MISSING_OPTIONAL_PROPERTIES_ERROR = 112
MISSING_SUPPLIER_PRICES_ERROR = 113
MISSING_STOCK_ERROR = 114
MISSING_LEAD_TIME_ERROR = 115
MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR = 116
VARIATION_MISMATCH_PRODUCT_TYPE_ERROR = 117
ITEMS_MISMATCH_PRODUCT_TYPE_ERROR = 118
BOM_MISMATCH_PRODUCT_TYPE_ERROR = 119
ITEMS_MISSING_MANDATORY_INFORMATION_ERROR = 120
VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR = 121
BOM_MISSING_MANDATORY_INFORMATION_ERROR = 122
DUPLICATE_VARIATIONS_ERROR = 123
NON_CONFIGURABLE_RULE_ERROR = 124

ERROR_TYPES = (
    (HAS_IMAGES_ERROR, _('Product is missing required images')),
    (MISSING_PRICES_ERROR, _("Product Missing Prices")),
    (INACTIVE_BILL_OF_MATERIALS_ERROR, _('Manufacturable Product has inactive bill of materials')),
    (INACTIVE_BUNDLE_ITEMS_ERROR, _('Bundle Product has inactive items')),
    (MISSING_VARIATION_ERROR, _('Product is missing required variations')),
    (MISSING_BUNDLE_ITEMS_ERROR, _('Bundle product is missing items')),
    (MISSING_BILL_OF_MATERIALS_ERROR, _('Manufacturable product is missing bill of materials')),
    (MISSING_SUPPLIER_PRODUCTS_ERROR, _('Product is missing supplier products')),
    (MISSING_EAN_CODE_ERROR, _('Product is missing an EAN code')),
    (MISSING_PRODUCT_TYPE_ERROR, _('Product is missing a required product type property')),
    (MISSING_REQUIRED_PROPERTIES_ERROR, _('Product is missing required properties')),
    (MISSING_OPTIONAL_PROPERTIES_ERROR, _('Product is missing optional properties')),
    (MISSING_SUPPLIER_PRICES_ERROR, _('Supplier product is missing required prices')),
    (MISSING_STOCK_ERROR, _('Product is active, missing stock, and does not allow backorder')),
    (MISSING_LEAD_TIME_ERROR, _('Product is missing lead time when out of stock')),
    (MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR, _('Manual price list price should have at least override price')),
    (VARIATION_MISMATCH_PRODUCT_TYPE_ERROR, _('Variations do not have the same product type')),
    (ITEMS_MISMATCH_PRODUCT_TYPE_ERROR, _('Items do not have the same product type')),
    (BOM_MISMATCH_PRODUCT_TYPE_ERROR, _('Bill of materials do not have the same product type')),
    (ITEMS_MISSING_MANDATORY_INFORMATION_ERROR, _('Items have inspectors missing mandatory information')),
    (VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR, _('Variations have inspectors missing mandatory information')),
    (BOM_MISSING_MANDATORY_INFORMATION_ERROR, _('Bill of materials have inspectors missing mandatory information')),
    (DUPLICATE_VARIATIONS_ERROR, _('Configurable product has duplicate variations')),
    (NON_CONFIGURABLE_RULE_ERROR, _('Configurable product has no applicable configurator rules')),
)


# BLOCKS CONFIG SECTION
has_image_block = {
    'error_code': HAS_IMAGES_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': REQUIRED,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

missing_prices_block = {
    'error_code': MISSING_PRICES_ERROR,
    'simple_product_applicability': REQUIRED,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': REQUIRED,
    'bundle_product_applicability': REQUIRED,
    'dropship_product_applicability': REQUIRED,
    'supplier_product_applicability': NONE,
}

inactive_pieces_block = {
    'error_code': INACTIVE_BILL_OF_MATERIALS_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': REQUIRED,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

inactive_bundle_items_block = {
    'error_code': INACTIVE_BUNDLE_ITEMS_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': REQUIRED,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

missing_variation_block = {
    'error_code': MISSING_VARIATION_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': REQUIRED,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

missing_bundle_items_block = {
    'error_code': MISSING_BUNDLE_ITEMS_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': OPTIONAL,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

missing_bill_of_materials_block = {
    'error_code': MISSING_BILL_OF_MATERIALS_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': OPTIONAL,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

missing_supplier_products_block = {
    'error_code': MISSING_SUPPLIER_PRODUCTS_ERROR,
    'simple_product_applicability': REQUIRED,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': REQUIRED,
    'supplier_product_applicability': NONE,
}

missing_ean_code_block = {
    'error_code': MISSING_EAN_CODE_ERROR,
    'simple_product_applicability': REQUIRED,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': REQUIRED,
    'bundle_product_applicability': REQUIRED,
    'dropship_product_applicability': REQUIRED,
    'supplier_product_applicability': NONE,
}

missing_product_type_block = {
    'error_code': MISSING_PRODUCT_TYPE_ERROR,
    'simple_product_applicability': REQUIRED,
    'configurable_product_applicability': REQUIRED,
    'manufacturable_product_applicability': REQUIRED,
    'bundle_product_applicability': REQUIRED,
    'dropship_product_applicability': REQUIRED,
    'supplier_product_applicability': NONE,
}

missing_required_properties_block = {
    'error_code': MISSING_REQUIRED_PROPERTIES_ERROR,
    'simple_product_applicability': REQUIRED,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': REQUIRED,
    'bundle_product_applicability': REQUIRED,
    'dropship_product_applicability': REQUIRED,
    'supplier_product_applicability': NONE,
}

missing_optional_properties_block = {
    'error_code': MISSING_OPTIONAL_PROPERTIES_ERROR,
    'simple_product_applicability': OPTIONAL,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': OPTIONAL,
    'bundle_product_applicability': OPTIONAL,
    'dropship_product_applicability': OPTIONAL,
    'supplier_product_applicability': NONE,
}

missing_supplier_prices_block = {
    'error_code': MISSING_SUPPLIER_PRICES_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': REQUIRED,
}

missing_stock_block = {
    'error_code': MISSING_STOCK_ERROR,
    'simple_product_applicability': OPTIONAL,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': OPTIONAL,
    'supplier_product_applicability': NONE,
}

missing_lead_time_block = {
    'error_code': MISSING_LEAD_TIME_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': OPTIONAL,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': OPTIONAL,
}

missing_manual_pricelist_override_block = {
    'error_code': MISSING_MANUAL_PRICELIST_OVERRIDE_ERROR,
    'simple_product_applicability': REQUIRED,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': REQUIRED,
    'bundle_product_applicability': REQUIRED,
    'dropship_product_applicability': REQUIRED,
    'supplier_product_applicability': NONE,
}

variation_mismatch_product_type_block = {
    'error_code': VARIATION_MISMATCH_PRODUCT_TYPE_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': REQUIRED,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

items_mismatch_product_type_block = {
    'error_code': ITEMS_MISMATCH_PRODUCT_TYPE_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': REQUIRED,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

bom_mismatch_product_type_block = {
    'error_code': BOM_MISMATCH_PRODUCT_TYPE_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': REQUIRED,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

items_missing_mandatory_information_block = {
    'error_code': ITEMS_MISSING_MANDATORY_INFORMATION_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': REQUIRED,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

variations_missing_mandatory_information_block = {
    'error_code': VARIATIONS_MISSING_MANDATORY_INFORMATION_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': REQUIRED,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

bom_missing_mandatory_information_block = {
    'error_code': BOM_MISSING_MANDATORY_INFORMATION_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': NONE,
    'manufacturable_product_applicability': REQUIRED,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

duplicate_variations_block = {
    'error_code': DUPLICATE_VARIATIONS_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': REQUIRED,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}

non_configurable_rule_block = {
    'error_code': NON_CONFIGURABLE_RULE_ERROR,
    'simple_product_applicability': NONE,
    'configurable_product_applicability': REQUIRED,
    'manufacturable_product_applicability': NONE,
    'bundle_product_applicability': NONE,
    'dropship_product_applicability': NONE,
    'supplier_product_applicability': NONE,
}


blocks = [
    has_image_block,
    missing_prices_block,
    inactive_pieces_block,
    inactive_bundle_items_block,
    missing_variation_block,
    missing_bundle_items_block,
    missing_bill_of_materials_block,
    missing_supplier_products_block,
    missing_ean_code_block,
    missing_product_type_block,
    missing_required_properties_block,
    missing_optional_properties_block,
    missing_supplier_prices_block,
    missing_stock_block,
    missing_lead_time_block,
    missing_manual_pricelist_override_block,
    variation_mismatch_product_type_block,
    items_mismatch_product_type_block,
    bom_mismatch_product_type_block,
    items_missing_mandatory_information_block,
    variations_missing_mandatory_information_block,
    bom_missing_mandatory_information_block,
    duplicate_variations_block,
    non_configurable_rule_block
]
