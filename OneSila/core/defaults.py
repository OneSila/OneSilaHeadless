def get_product_type_name(language):
    names = {
        'en': 'Product Type',
        'fr': 'Type de produit',
        'nl': 'Producttype',
        'de': 'Produkttyp',
        'it': 'Tipo di prodotto',
        'es': 'Tipo de producto',
        'pt': 'Tipo de produto',
        'pt-br': 'Tipo de produto',
        'pl': 'Rodzaj produktu',
        'ro': 'Tip de produs',
        'bg': 'Тип продукт',
        'hr': 'Vrsta proizvoda',
        'cs': 'Typ produktu',
        'da': 'Produkttype',
        'et': 'Toodetüüp',
        'fi': 'Tuotetyyppi',
        'el': 'Τύπος προϊόντος',
        'hu': 'Terméktípus',
        'lv': 'Produkta veids',
        'lt': 'Produkto tipas',
        'sk': 'Typ produktu',
        'sl': 'Vrsta izdelka',
        'sv': 'Produkttyp',
        'th': 'ประเภทสินค้า',
        'ja': '製品タイプ',
        'zh-hans': '产品类型',
        'hi': 'उत्पाद प्रकार',
        'ru': 'Тип продукта',
        'af': 'Produk Tipe',
        'ar': 'نوع المنتج',
        'he': 'סוג מוצר',
        'tr': 'Ürün Türü',
        'id': 'Jenis Produk',
        'ko': '제품 유형',
        'ms': 'Jenis Produk',
        'vi': 'Loại sản phẩm',
        'fa': 'نوع محصول',
        'ur': 'مصنوع کی قسم',
    }
    return names.get(language, names['en'])


def get_brand_name(language):
    names = {
        'en': 'Brand',
        'fr': 'Marque',
        'nl': 'Merk',
        'de': 'Marke',
        'it': 'Marca',
        'es': 'Marca',
        'pt': 'Marca',
        'pt-br': 'Marca',
        'pl': 'Marka',
        'ro': 'Brand',
        'bg': 'Марка',
        'hr': 'Marka',
        'cs': 'Značka',
        'da': 'Mærke',
        'et': 'Bränd',
        'fi': 'Brändi',
        'el': 'Μάρκα',
        'hu': 'Márka',
        'lv': 'Zīmols',
        'lt': 'Prekės ženklas',
        'sk': 'Značka',
        'sl': 'Znamka',
        'sv': 'Märke',
        'th': 'แบรนด์',
        'ja': 'ブランド',
        'zh-hans': '品牌',
        'hi': 'ब्रांड',
        'ru': 'Бренд',
        'af': 'Handelsmerk',
        'ar': 'العلامة التجارية',
        'he': 'מותג',
        'tr': 'Marka',
        'id': 'Merek',
        'ko': '브랜드',
        'ms': 'Jenama',
        'vi': 'Thương hiệu',
        'fa': 'برند',
        'ur': 'برانڈ',
    }
    return names.get(language, names['en'])


DASHBOARD_PRODUCTS_QUERY = (
    "query ProductsDashboardCards($errorCode: String!) {"
    "  products("
    "    filters: {inspectorNotSuccessfullyCodeError: $errorCode, active: {exact: true}}"
    "  ) {"
    "    totalCount"
    "    __typename"
    "  }"
    "}"
)

PRODUCTS_DASHBOARD_URL_TEMPLATE = (
    "/products?inspectorNotSuccessfullyCodeError={error_code}&active=true"
)

DASHBOARD_PROPERTIES_MISSING_MAIN_TRANSLATIONS_QUERY = (
    "query DashboardPropertiesMissingMainTranslations {"
    " properties(filters: { missingMainTranslation: true }) {"
    "   totalCount"
    " }"
    "}"
)

DASHBOARD_PROPERTIES_MISSING_TRANSLATIONS_QUERY = (
    "query DashboardPropertiesMissingTranslations {"
    " properties(filters: { missingTranslations: true }) {"
    "   totalCount"
    " }"
    "}"
)

DASHBOARD_PROPERTY_SELECT_VALUES_MISSING_MAIN_TRANSLATIONS_QUERY = (
    "query DashboardPropertySelectValuesMissingMainTranslations {"
    " propertySelectValues(filters: { missingMainTranslation: true }) {"
    "   totalCount"
    " }"
    "}"
)

DASHBOARD_PROPERTY_SELECT_VALUES_MISSING_TRANSLATIONS_QUERY = (
    "query DashboardPropertySelectValuesMissingTranslations {"
    " propertySelectValues(filters: { missingTranslations: true }) {"
    "   totalCount"
    " }"
    "}"
)

PROPERTIES_DASHBOARD_URL = "/properties/properties"
PROPERTY_SELECT_VALUES_DASHBOARD_URL = "/properties/property-select-values"


DASHBOARD_SECTION_DEFINITIONS = [
    {
        "identifier": "products",
        "title": "Products cards",
        "description": (
            "Ensure all product information is accurate and up-to-date to maintain "
            "inventory integrity and optimize sales performance."
        ),
        "sort_order": 1,
        "cards": [
            {
                "title": "Products Missing Images",
                "description": "Add at least one image to these products.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "101"},
                "query_key": "products",
                "sort_order": 1,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="101"),
            },
            {
                "title": "Products Missing Default Prices",
                "description": "Ensure these products have valid default prices.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "102"},
                "query_key": "products",
                "sort_order": 2,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="102"),
            },
            {
                "title": "Products Missing Variations",
                "description": "Add required variations to these configurable products.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "105"},
                "query_key": "products",
                "sort_order": 3,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="105"),
            },
            {
                "title": "Product Type Missing",
                "description": "Assign a product type to these products.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "110"},
                "query_key": "products",
                "sort_order": 4,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="110"),
            },
            {
                "title": "Products Missing Required Properties",
                "description": "Assign all required properties to these products.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "111"},
                "query_key": "products",
                "sort_order": 5,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="111"),
            },
            {
                "title": "Variation Product Type Mismatch",
                "description": "Ensure all variations have the same product type.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "117"},
                "query_key": "products",
                "sort_order": 6,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="117"),
            },
            {
                "title": "Configurable Product Missing Rule Configuration",
                "description": "Define at least one configurator required item for these configurable products.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "124"},
                "query_key": "products",
                "sort_order": 7,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="124"),
            },
            {
                "title": "Products with Amazon Validation Issues",
                "description": "Review Amazon validation issues for these products in the Amazon tab.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "125"},
                "query_key": "products",
                "sort_order": 8,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="125"),
            },
            {
                "title": "Products with Amazon Remote Issues",
                "description": "Check the Amazon tab for remote issues reported by Amazon and resolve them.",
                "color": "RED",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "126"},
                "query_key": "products",
                "sort_order": 9,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="126"),
            },
            {
                "title": "Products Missing EAN Codes",
                "description": "Provide EAN codes for these products.",
                "color": "ORANGE",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "109"},
                "query_key": "products",
                "sort_order": 10,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="109"),
            },
            {
                "title": "Products Missing Optional Properties",
                "description": "Assign optional properties to these products as needed.",
                "color": "ORANGE",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "112"},
                "query_key": "products",
                "sort_order": 11,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="112"),
            },
            {
                "title": "Manual Price List Prices Missing Override Prices",
                "description": "Add override prices to manual price list prices where auto-update is disabled.",
                "color": "ORANGE",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "116"},
                "query_key": "products",
                "sort_order": 12,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="116"),
            },
            {
                "title": "Configurable Products with Duplicate Variations",
                "description": "Ensure variations in these configurable products have unique required properties.",
                "color": "YELLOW",
                "query": DASHBOARD_PRODUCTS_QUERY,
                "variables": {"errorCode": "123"},
                "query_key": "products",
                "sort_order": 13,
                "url_path": PRODUCTS_DASHBOARD_URL_TEMPLATE.format(error_code="123"),
            },
        ],
    },
    {
        "identifier": "general",
        "title": "General cards",
        "description": "Improve your data quality by resolving the following issues.",
        "sort_order": 2,
        "cards": [
            {
                "title": "Properties Missing Main Translation",
                "description": "These properties lack translations for your company's main language.",
                "color": "YELLOW",
                "query": DASHBOARD_PROPERTIES_MISSING_MAIN_TRANSLATIONS_QUERY,
                "query_key": "properties",
                "sort_order": 1,
                "url_path": f"{PROPERTIES_DASHBOARD_URL}?missingMainTranslation=true",
            },
            {
                "title": "Properties Missing Translations",
                "description": "These properties are not translated into all required languages.",
                "color": "YELLOW",
                "query": DASHBOARD_PROPERTIES_MISSING_TRANSLATIONS_QUERY,
                "query_key": "properties",
                "sort_order": 2,
                "url_path": f"{PROPERTIES_DASHBOARD_URL}?missingTranslations=true",
            },
            {
                "title": "Select Values Missing Main Language",
                "description": "Some select values lack translations for your company's main language.",
                "color": "YELLOW",
                "query": DASHBOARD_PROPERTY_SELECT_VALUES_MISSING_MAIN_TRANSLATIONS_QUERY,
                "query_key": "propertySelectValues",
                "sort_order": 3,
                "url_path": f"{PROPERTY_SELECT_VALUES_DASHBOARD_URL}?missingMainTranslation=true",
            },
            {
                "title": "Select Values Missing Translations",
                "description": "Some select values are missing translations for all required languages.",
                "color": "YELLOW",
                "query": DASHBOARD_PROPERTY_SELECT_VALUES_MISSING_TRANSLATIONS_QUERY,
                "query_key": "propertySelectValues",
                "sort_order": 4,
                "url_path": f"{PROPERTY_SELECT_VALUES_DASHBOARD_URL}?missingTranslations=true",
            },
        ],
    },
]
