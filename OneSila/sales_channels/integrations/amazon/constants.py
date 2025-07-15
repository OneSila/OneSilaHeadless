SELLER_CENTRAL_URLS = {
    "CA": "https://sellercentral.amazon.ca",
    "US": "https://sellercentral.amazon.com",
    "MX": "https://sellercentral.amazon.com.mx",
    "BR": "https://sellercentral.amazon.com.br",
    "IE": "https://sellercentral.amazon.ie",
    "ES": "https://sellercentral-europe.amazon.com",
    "GB": "https://sellercentral-europe.amazon.com",
    "FR": "https://sellercentral-europe.amazon.com",
    "BE": "https://sellercentral.amazon.com.be",
    "NL": "https://sellercentral.amazon.nl",
    "DE": "https://sellercentral-europe.amazon.com",
    "IT": "https://sellercentral-europe.amazon.com",
    "SE": "https://sellercentral.amazon.se",
    "ZA": "https://sellercentral.amazon.co.za",
    "PL": "https://sellercentral.amazon.pl",
    "EG": "https://sellercentral.amazon.eg",
    "TR": "https://sellercentral.amazon.com.tr",
    "SA": "https://sellercentral.amazon.sa",
    "AE": "https://sellercentral.amazon.ae",
    "IN": "https://sellercentral.amazon.in",
    "SG": "https://sellercentral.amazon.sg",
    "AU": "https://sellercentral.amazon.com.au",
    "JP": "https://sellercentral.amazon.co.jp",
}

AMAZON_OAUTH_TOKEN_URL = "https://api.amazon.com/auth/o2/token"


AMAZON_LOCALE_MAPPING = {
    'en': 'en_US',
    'fr': 'fr_FR',
    'nl': 'nl_NL',
    'de': 'de_DE',
    'it': 'it_IT',
    'es': 'es_ES',
    'pt': 'pt_PT',
    'pt-br': 'pt_BR',
    'pl': 'pl_PL',
    'ro': 'ro_RO',
    'bg': 'bg_BG',
    'hr': 'hr_HR',
    'cs': 'cs_CZ',
    'da': 'da_DK',
    'et': 'et_EE',
    'fi': 'fi_FI',
    'el': 'el_GR',
    'hu': 'hu_HU',
    'lv': 'lv_LV',
    'lt': 'lt_LT',
    'sk': 'sk_SK',
    'sl': 'sl_SI',
    'sv': 'sv_SE',
    'th': 'th_TH',
    'ja': 'ja_JP',
    'zh-hans': 'zh_CN',
    'hi': 'hi_IN',
    'ru': 'ru_RU',
    'af': 'af_ZA',
    'ar': 'ar_SA',
    'he': 'he_IL',
    'tr': 'tr_TR',
    'id': 'id_ID',
    'ko': 'ko_KR',
    'ms': 'ms_MY',
    'vi': 'vi_VN',
    'fa': 'fa_IR',
    'ur': 'ur_PK',
}

AMAZON_INTERNAL_PROPERTIES = [
    # Image handling (via media pipeline)
    'main_offer_image_locator', 'other_offer_image_locator_1', 'other_offer_image_locator_2',
    'other_offer_image_locator_3', 'other_offer_image_locator_4', 'other_offer_image_locator_5',
    'main_product_image_locator', 'other_product_image_locator_1', 'other_product_image_locator_2',
    'other_product_image_locator_3', 'other_product_image_locator_4', 'other_product_image_locator_5',
    'other_product_image_locator_6', 'other_product_image_locator_7', 'other_product_image_locator_8',
    'swatch_product_image_locator', 'image_locator_ps01', 'image_locator_ps02',
    'image_locator_ps03', 'image_locator_ps04', 'image_locator_ps05', 'image_locator_ps06',

    'item_name', 'package_level', 'package_contains_sku', 'purchasable_offer',
    'condition_note', 'list_price', 'max_order_quantity', 'product_description', 'bullet_point',
    'child_parent_sku_relationship', 'variation_theme', 'master_pack_layers_per_pallet_quantity',
    'master_packs_per_layer_quantity', 'is_oem_sourced_product', 'parentage_level',

    # Auto-linking/ASIN suggestion
    'merchant_suggested_asin', 'externally_assigned_product_identifier',
    'supplier_declared_has_product_identifier_exemption',

    # Amazon-only compliance metadata (for now)
    'compliance_media', 'gpsr_safety_attestation', 'gpsr_manufacturer_reference',
    'dsa_responsible_party_address', 'epr_product_packaging', 'national_stock_number',
    'ghs', 'ghs_chemical_h_code',

    # Fulfillment-specific (not PIM core)
    'fulfillment_availability', 'merchant_shipping_group', 'merchant_release_date',
    'skip_offer', 'supplemental_condition_information', 'uvp_list_price'
]