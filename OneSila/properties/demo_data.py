from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator
from properties.models import Property, PropertyTranslation, PropertySelectValue, PropertySelectValueTranslation, ProductPropertiesRule, \
    ProductPropertiesRuleItem

registry = DemoDataLibrary()


@registry.register_private_app
def create_property_structure(multi_tenant_company):
    """Create properties and related data for the demo."""

    # Create Properties with translations
    properties_data = [
        {'type': Property.TYPES.SELECT, 'name': 'Size', 'values': ['Small', 'Medium', 'Large']},
        {'type': Property.TYPES.SELECT, 'name': 'Color', 'values': ['Red', 'Green', 'Blue']},
        {'type': Property.TYPES.SELECT, 'name': 'Materials', 'values': ['Wood', 'Metal', 'Plastic']},
        {'type': Property.TYPES.INT, 'name': 'Weight'},
        {'type': Property.TYPES.DATE, 'name': 'Manufacture Date'}
    ]

    for prop_data in properties_data:
        property = Property.objects.create(
            multi_tenant_company=multi_tenant_company,
            type=prop_data['type']
        )

        translation = PropertyTranslation.objects.create(
            multi_tenant_company=multi_tenant_company,
            property=property,
            language='en',
            name=prop_data['name']
        )

        registry.create_demo_data_relation(translation)
        registry.create_demo_data_relation(property)

        # Create select values for properties that have them
        if 'values' in prop_data:
            for value in prop_data['values']:
                select_value = PropertySelectValue.objects.create(
                    property=property,
                    multi_tenant_company=multi_tenant_company,
                )
                registry.create_demo_data_relation(select_value)

                translation = PropertySelectValueTranslation.objects.create(
                    multi_tenant_company=multi_tenant_company,
                    propertyselectvalue=select_value,
                    language='en',
                    value=value
                )
                registry.create_demo_data_relation(translation)

    product_type_property = Property.objects.get(is_product_type=True, multi_tenant_company=multi_tenant_company)
    product_types = ['Table', 'Chair', 'Bed']
    for value in product_types:
        prop_select_value = PropertySelectValue.objects.create(
            property=product_type_property,
            multi_tenant_company=multi_tenant_company,
        )

        registry.create_demo_data_relation(prop_select_value)

        translation = PropertySelectValueTranslation.objects.create(
            multi_tenant_company=multi_tenant_company,
            propertyselectvalue=prop_select_value,
            language='en',
            value=value
        )
        registry.create_demo_data_relation(translation)

        if value == 'Table':
            product_properties_rule = ProductPropertiesRule.objects.create(
                multi_tenant_company=multi_tenant_company,
                product_type=prop_select_value
            )
            registry.create_demo_data_relation(product_properties_rule)

            item_one = ProductPropertiesRuleItem.objects.create(
                multi_tenant_company=multi_tenant_company,
                rule=product_properties_rule,
                property=PropertyTranslation.objects.get(multi_tenant_company=multi_tenant_company, name='Color').property,
                type=ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR
            )
            item_two = ProductPropertiesRuleItem.objects.create(
                multi_tenant_company=multi_tenant_company,
                rule=product_properties_rule,
                property=PropertyTranslation.objects.get(multi_tenant_company=multi_tenant_company, name='Materials').property,
                type=ProductPropertiesRuleItem.OPTIONAL
            )

            registry.create_demo_data_relation(item_one)
            registry.create_demo_data_relation(item_two)
