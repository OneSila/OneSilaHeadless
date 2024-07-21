def get_product_type_name(language):
    names = {
        'en': 'Product Type',
        'nl': 'Producttype',
    }
    return names.get(language, 'Product Type')