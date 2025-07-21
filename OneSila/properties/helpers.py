def get_product_properties_dict(product) -> dict[str, list[str]]:
    """
    Fetch all properties and their values for a given product.

    :param product: product instance
    :return: Dictionary of properties and their values

    The return value looks like:
    {
        "property_name": [
            "value1",
            "value2",
            "valueN"
        ]
    }
    """
    # TODO: This should really support languages.
    from properties.models import ProductProperty, Property

    properties = (
        ProductProperty.objects.filter(product=product)
        .select_related("property", "value_select")  # Optimize DB queries
        .prefetch_related("value_multi_select")  # Prefetch related multi-select values
    )

    properties_dict = {}
    for prop in properties:
        prop_type = prop.property.type

        if prop_type == Property.TYPES.MULTISELECT:
            values = {value.value for value in prop.value_multi_select.all()}  # Use a set for uniqueness
        elif prop_type == Property.TYPES.SELECT:
            values = {prop.value_select.value} if prop.value_select else set()
        elif prop_type in {
            Property.TYPES.INT, Property.TYPES.FLOAT, Property.TYPES.TEXT,
            Property.TYPES.BOOLEAN, Property.TYPES.DATE, Property.TYPES.DATETIME
        }:
            values = {str(prop.value)} if getattr(prop, "value", None) is not None else set()
        else:
            values = set()

        properties_dict[str(prop.property.name)] = list(values)  # Convert back to a list for consistency

    return properties_dict


def generate_unique_internal_name(name, multi_tenant_company, instance_id=None):
    """Return a unique internal name for a property."""
    from django.utils.text import slugify
    from .models import Property

    base_name = slugify(name).replace('-', '_')
    internal_name = base_name
    counter = 1

    qs = Property.objects.filter(multi_tenant_company=multi_tenant_company)
    if instance_id:
        qs = qs.exclude(id=instance_id)

    while qs.filter(internal_name=internal_name).exists():
        internal_name = f"{base_name}_{counter}"
        counter += 1

    return internal_name
