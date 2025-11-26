# Helper functions for Woocommerce integration

def format_product_data(product_data):
    """
    Format product data for Woocommerce API
    """
    # Add implementation
    return product_data


def format_order_data(order_data):
    """
    Format order data for Woocommerce API
    """
    # Add implementation
    return order_data


def convert_fields_to_int(data: dict, fields_convert_to_int: list) -> dict:
    """
    Convert fields to int, with nested  __ support.
    eg:
    data = {'id': 2992, 'attributes': {'id': '29', 'name': 'test'}}
    fields_convert_to_int = ['attributes__id']

    will be converted to:
    data = {'id': 2992, 'attributes': {'id': 29, 'name': 'test'}}
    """
    for field_path in fields_convert_to_int:
        keys = field_path.split('__')
        current = data

        try:
            for key in keys[:-1]:
                current = current[key]
            final_key = keys[-1]
            if final_key in current:
                current[final_key] = int(current[final_key])
        except (KeyError, TypeError, ValueError):
            # Silently skip if the path is invalid or value can't be converted
            continue

    return data


def clearout_none_values(data: dict) -> dict:
    """
    Clear out none values from the data.
    """
    return {k: v for k, v in data.items() if v is not None}


def convert_fields_to_string(data, field_convert_to_string):
    """
    Convert fields to string, with nested  __ support.
    eg:
    data = {'id': 2992, 'attributes': {'id': '29', 'name': 'test'}}
    field_convert_to_string = ['attributes__name', 'name]

    will be converted to:
    """
    for field_path in field_convert_to_string:
        keys = field_path.split('__')
        current = data

        try:
            for key in keys[:-1]:
                current = current[key]
            final_key = keys[-1]
            if final_key in current:
                current[final_key] = str(current[final_key])
        except (KeyError, TypeError):
            continue  # Silently skip if path is invalid

    return data


def raise_for_required_fields(data: dict, required_fields: list):
    """
    Raise an error if any of the required fields are not present in the data.
    """
    # Handle nested fields with __ notation
    missing_fields = []

    for field in required_fields:
        keys = field.split('__')
        current = data

        try:
            for key in keys[:-1]:
                current = current[key]
            final_key = keys[-1]
            if final_key not in current:
                missing_fields.append(field)
        except (KeyError, TypeError):
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(f"The following fields are required and currently not presented in the payload: {missing_fields}")

    return data
