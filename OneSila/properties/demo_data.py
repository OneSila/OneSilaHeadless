from core.demo_data import DemoDataLibrary, baker, fake, PrivateDataGenerator, PublicDataGenerator, CreatePrivateDataRelationMixin
from properties.models import Property, PropertyTranslation, PropertySelectValue, PropertySelectValueTranslation, ProductPropertiesRule, \
    ProductPropertiesRuleItem

registry = DemoDataLibrary()


def create_property_structure(multi_tenant_company):
    """Create properties and related data for the demo."""

    # Create Properties with translations
    properties_data = [
        {'type': Property.TYPES.SELECT, 'name': 'Size', 'values': ['Small', 'Medium', 'Large'], 'internal_name': 'size'},
        {'type': Property.TYPES.SELECT, 'name': 'Color', 'values': ['Red', 'Green', 'Blue'], 'internal_name': 'color'},
        {'type': Property.TYPES.SELECT, 'name': 'Materials', 'values': ['Wood', 'Metal', 'Plastic'], 'internal_name': 'materials'},
        {'type': Property.TYPES.FLOAT, 'name': 'Weight', 'internal_name': 'weight'},
        {'type': Property.TYPES.DATE, 'name': 'Manufacture Date', 'internal_name': 'manufacture_date'},
        {'type': Property.TYPES.MULTISELECT, 'name': 'Usage',
         'values': ['Indoor', 'Outdoor', 'Office', 'Garden', 'Restaurant', 'Hotel'], 'internal_name': 'usage'},
    ]

    property_map = {}

    for prop_data in properties_data:
        property, created = Property.objects.get_or_create(
            multi_tenant_company=multi_tenant_company,
            type=prop_data['type'],
            internal_name=prop_data['internal_name']
        )

        if not created:
            property_map[prop_data['name']] = property
            continue

        CreatePrivateDataRelationMixin.create_demo_data_relation(property)

        translation = PropertyTranslation.objects.create(
            multi_tenant_company=multi_tenant_company,
            property=property,
            language='en',
            name=prop_data['name']
        )
        CreatePrivateDataRelationMixin.create_demo_data_relation(translation)

        registry.create_demo_data_relation(translation)
        registry.create_demo_data_relation(property)

        property_map[prop_data['name']] = property

        # Create select values for properties that have them
        if 'values' in prop_data:
            for value in prop_data['values']:
                select_value = PropertySelectValue.objects.create(
                    property=property,
                    multi_tenant_company=multi_tenant_company,
                )
                CreatePrivateDataRelationMixin.create_demo_data_relation(select_value)
                registry.create_demo_data_relation(select_value)

                translation = PropertySelectValueTranslation.objects.create(
                    multi_tenant_company=multi_tenant_company,
                    propertyselectvalue=select_value,
                    language='en',
                    value=value
                )
                CreatePrivateDataRelationMixin.create_demo_data_relation(translation)
                registry.create_demo_data_relation(translation)

    product_type_property = Property.objects.get(is_product_type=True, multi_tenant_company=multi_tenant_company)
    product_types = ['Table', 'Chair', 'Bed']

    for value in product_types:
        prop_select_value = PropertySelectValue.objects.create(
            property=product_type_property,
            multi_tenant_company=multi_tenant_company,
        )

        CreatePrivateDataRelationMixin.create_demo_data_relation(prop_select_value)
        registry.create_demo_data_relation(prop_select_value)

        translation = PropertySelectValueTranslation.objects.create(
            multi_tenant_company=multi_tenant_company,
            propertyselectvalue=prop_select_value,
            language='en',
            value=value
        )

        CreatePrivateDataRelationMixin.create_demo_data_relation(translation)
        registry.create_demo_data_relation(translation)

        # Create Product Properties Rule
        product_properties_rule, created = ProductPropertiesRule.objects.get_or_create(
            multi_tenant_company=multi_tenant_company,
            product_type=prop_select_value
        )
        registry.create_demo_data_relation(product_properties_rule)
        if created:
            CreatePrivateDataRelationMixin.create_demo_data_relation(product_properties_rule)

        # Assign properties based on type
        property_assignments = {
            "Table": [
                (property_map['Color'], ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR),
                (property_map['Materials'], ProductPropertiesRuleItem.OPTIONAL),
                (property_map['Weight'], ProductPropertiesRuleItem.REQUIRED),
                (property_map['Usage'], ProductPropertiesRuleItem.OPTIONAL),
            ],
            "Chair": [
                (property_map['Color'], ProductPropertiesRuleItem.REQUIRED_IN_CONFIGURATOR),
                (property_map['Materials'], ProductPropertiesRuleItem.REQUIRED),
                (property_map['Usage'], ProductPropertiesRuleItem.OPTIONAL),
            ],
            "Bed": [
                (property_map['Size'], ProductPropertiesRuleItem.REQUIRED),
                (property_map['Materials'], ProductPropertiesRuleItem.REQUIRED),
                (property_map['Manufacture Date'], ProductPropertiesRuleItem.OPTIONAL),
                (property_map['Usage'], ProductPropertiesRuleItem.OPTIONAL),
            ],
        }

        for prop, rule_type in property_assignments.get(value, []):
            rule_item = ProductPropertiesRuleItem.objects.create(
                multi_tenant_company=multi_tenant_company,
                rule=product_properties_rule,
                property=prop,
                type=rule_type
            )

            CreatePrivateDataRelationMixin.create_demo_data_relation(rule_item)
            registry.create_demo_data_relation(rule_item)


create_property_structure.priority = 100
registry.register_private_app(create_property_structure)
