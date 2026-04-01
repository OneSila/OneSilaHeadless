def get_product_type_name(language):
    names = {
        'en-gb': 'Product Type',
        'fr-fr': 'Type de produit',
        'nl-nl': 'Producttype',
        'de-de': 'Produkttyp',
        'it-it': 'Tipo di prodotto',
        'es-es': 'Tipo de producto',
        'pt-pt': 'Tipo de produto',
        'pt-br': 'Tipo de produto',
        'pl-pl': 'Rodzaj produktu',
        'ro-ro': 'Tip de produs',
        'bg-bg': 'Тип продукт',
        'hr-hr': 'Vrsta proizvoda',
        'cs-cz': 'Typ produktu',
        'da-dk': 'Produkttype',
        'et-ee': 'Toodetüüp',
        'fi-fi': 'Tuotetyyppi',
        'el-gr': 'Τύπος προϊόντος',
        'hu-hu': 'Terméktípus',
        'lv-lv': 'Produkta veids',
        'lt-lt': 'Produkto tipas',
        'sk-sk': 'Typ produktu',
        'sl-si': 'Vrsta izdelka',
        'sv-se': 'Produkttyp',
        'th-th': 'ประเภทสินค้า',
        'ja-jp': '製品タイプ',
        'zh-cn': '产品类型',
        'hi-in': 'उत्पाद प्रकार',
        'ru-ru': 'Тип продукта',
        'af-za': 'Produk Tipe',
        'ar-sa': 'نوع المنتج',
        'he-il': 'סוג מוצר',
        'tr-tr': 'Ürün Türü',
        'id-id': 'Jenis Produk',
        'ko-kr': '제품 유형',
        'ms-my': 'Jenis Produk',
        'vi-vn': 'Loại sản phẩm',
        'fa-ir': 'نوع محصول',
        'ur-pk': 'مصنوع کی قسم',
    }
    return names.get(language, names['en-gb'])


def get_brand_name(language):
    names = {
        'en-gb': 'Brand',
        'fr-fr': 'Marque',
        'nl-nl': 'Merk',
        'de-de': 'Marke',
        'it-it': 'Marca',
        'es-es': 'Marca',
        'pt-pt': 'Marca',
        'pt-br': 'Marca',
        'pl-pl': 'Marka',
        'ro-ro': 'Brand',
        'bg-bg': 'Марка',
        'hr-hr': 'Marka',
        'cs-cz': 'Značka',
        'da-dk': 'Mærke',
        'et-ee': 'Bränd',
        'fi-fi': 'Brändi',
        'el-gr': 'Μάρκα',
        'hu-hu': 'Márka',
        'lv-lv': 'Zīmols',
        'lt-lt': 'Prekės ženklas',
        'sk-sk': 'Značka',
        'sl-si': 'Znamka',
        'sv-se': 'Märke',
        'th-th': 'แบรนด์',
        'ja-jp': 'ブランド',
        'zh-cn': '品牌',
        'hi-in': 'ब्रांड',
        'ru-ru': 'Бренд',
        'af-za': 'Handelsmerk',
        'ar-sa': 'العلامة التجارية',
        'he-il': 'מותג',
        'tr-tr': 'Marka',
        'id-id': 'Merek',
        'ko-kr': '브랜드',
        'ms-my': 'Jenama',
        'vi-vn': 'Thương hiệu',
        'fa-ir': 'برند',
        'ur-pk': 'برانڈ',
    }
    return names.get(language, names['en-gb'])


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
